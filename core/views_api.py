from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import (
    Pedido, Entregador, AceitePedido, AvaliacaoEntregador, 
    OcorrenciaEntrega, Restaurante
)
from .serializers import (
    PedidoSerializer, EntregadorSerializer, AceitePedidoSerializer,
    AvaliacaoEntregadorSerializer, OcorrenciaEntregaSerializer,
    AlterarStatusPedidoSerializer, AtribuirEntregadorSerializer,
    RegistrarOcorrenciaSerializer, PedidosDisponiveisSerializer
)

User = get_user_model()


class IsEntregadorOrReadOnly(permissions.BasePermission):
    """Permissão para entregadores"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (request.user.is_authenticated and 
                request.user.tipo_usuario == 'entregador')


class IsLojistaOrSuperAdmin(permissions.BasePermission):
    """Permissão para lojistas ou super admin"""
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.tipo_usuario in ['lojista', 'superadmin'])


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.tipo_usuario == 'entregador':
            # Entregador vê apenas seus pedidos
            try:
                entregador = user.entregador
                return Pedido.objects.filter(entregador=entregador).order_by('-created_at')
            except Entregador.DoesNotExist:
                return Pedido.objects.none()
                
        elif user.tipo_usuario in ['lojista', 'funcionario', 'gerente']:
            # Lojista vê pedidos dos seus restaurantes
            restaurantes = user.restaurantes.all()
            return Pedido.objects.filter(restaurante__in=restaurantes).order_by('-created_at')
            
        elif user.tipo_usuario == 'superadmin':
            # Super admin vê todos
            return Pedido.objects.all().order_by('-created_at')
            
        else:
            # Cliente vê apenas seus pedidos
            return Pedido.objects.filter(cliente=user).order_by('-created_at')

    @action(detail=False, methods=['get'], permission_classes=[IsEntregadorOrReadOnly])
    def disponiveis(self, request):
        """Lista pedidos disponíveis para aceite pelos entregadores"""
        pedidos = Pedido.objects.filter(
            status='aguardando_entregador',
            tipo_entrega='delivery'
        ).order_by('-created_at')
        
        serializer = PedidosDisponiveisSerializer(pedidos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsEntregadorOrReadOnly])
    def aceitar(self, request, pk=None):
        """Entregador aceita um pedido"""
        pedido = self.get_object()
        
        # Verificar se o usuário é um entregador
        try:
            entregador = request.user.entregador
        except Entregador.DoesNotExist:
            return Response(
                {'erro': 'Usuário não é um entregador cadastrado.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar se o entregador está disponível
        if not entregador.disponivel or entregador.em_pausa:
            return Response(
                {'erro': 'Entregador não está disponível.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se o pedido pode ser aceito
        if pedido.status != 'aguardando_entregador':
            return Response(
                {'erro': 'Este pedido não está disponível para aceite.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aceitar o pedido atomicamente
        with transaction.atomic():
            # Verificar novamente se ainda está disponível (race condition)
            pedido.refresh_from_db()
            if pedido.status != 'aguardando_entregador':
                return Response(
                    {'erro': 'Este pedido já foi aceito por outro entregador.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Atribuir entregador e alterar status
            pedido.entregador = entregador
            pedido.status = 'em_entrega'
            pedido.save()
            
            # Registrar aceite
            AceitePedido.objects.create(
                pedido=pedido,
                entregador=entregador,
                status='aceito'
            )
        
        # TODO: Enviar notificação para lojista e cliente
        
        return Response({
            'sucesso': 'Pedido aceito com sucesso!',
            'pedido': PedidoSerializer(pedido).data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsLojistaOrSuperAdmin])
    def atribuir_entregador(self, request, pk=None):
        """Lojista atribui manualmente um entregador ao pedido"""
        pedido = self.get_object()
        serializer = AtribuirEntregadorSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        entregador_id = serializer.validated_data['entregador_id']
        entregador = get_object_or_404(Entregador, id=entregador_id)
        
        if pedido.status not in ['aguardando_entregador', 'pronto']:
            return Response(
                {'erro': 'Não é possível atribuir entregador neste status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            pedido.entregador = entregador
            pedido.status = 'em_entrega'
            pedido.save()
            
            AceitePedido.objects.create(
                pedido=pedido,
                entregador=entregador,
                status='aceito',
                observacoes=serializer.validated_data.get('observacoes', 'Atribuição manual pelo lojista')
            )
        
        # TODO: Enviar notificação para entregador
        
        return Response({
            'sucesso': 'Entregador atribuído com sucesso!',
            'pedido': PedidoSerializer(pedido).data
        })

    @action(detail=True, methods=['post'])
    def alterar_status(self, request, pk=None):
        """Altera o status do pedido"""
        pedido = self.get_object()
        serializer = AlterarStatusPedidoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        novo_status = serializer.validated_data['status']
        
        # Validações de transição de status
        status_anteriores = {
            'confirmado': ['pendente'],
            'preparando': ['confirmado'],
            'pronto': ['preparando'],
            'aguardando_entregador': ['pronto'],
            'em_entrega': ['aguardando_entregador'],
            'entregue': ['em_entrega'],
            'cancelado': ['pendente', 'confirmado', 'preparando']
        }
        
        if novo_status in status_anteriores:
            if pedido.status not in status_anteriores[novo_status]:
                return Response(
                    {'erro': f'Não é possível alterar de {pedido.get_status_display()} para {dict(Pedido.STATUS_CHOICES)[novo_status]}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Salvar status anterior e atualizar
        status_anterior = pedido.status
        pedido.status = novo_status
        
        # Definir data de confirmação/entrega
        if novo_status == 'confirmado' and not pedido.data_confirmacao:
            pedido.data_confirmacao = timezone.now()
        elif novo_status == 'entregue' and not pedido.data_entrega:
            pedido.data_entrega = timezone.now()
            
        pedido.observacoes_internas = serializer.validated_data.get('observacoes', '')
        pedido.save()
        
        # Criar histórico
        from .models import HistoricoStatusPedido
        HistoricoStatusPedido.objects.create(
            pedido=pedido,
            status_anterior=status_anterior,
            status_novo=novo_status,
            usuario=request.user,
            observacoes=serializer.validated_data.get('observacoes', '')
        )
        
        # Atualizar contador de entregas do entregador
        if novo_status == 'entregue' and pedido.entregador:
            pedido.entregador.total_entregas += 1
            pedido.entregador.save()
        
        return Response({
            'sucesso': f'Status alterado para {dict(Pedido.STATUS_CHOICES)[novo_status]}',
            'pedido': PedidoSerializer(pedido).data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsEntregadorOrReadOnly])
    def registrar_ocorrencia(self, request, pk=None):
        """Entregador registra uma ocorrência"""
        pedido = self.get_object()
        
        try:
            entregador = request.user.entregador
        except Entregador.DoesNotExist:
            return Response(
                {'erro': 'Usuário não é um entregador cadastrado.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if pedido.entregador != entregador:
            return Response(
                {'erro': 'Você não é o entregador responsável por este pedido.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RegistrarOcorrenciaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ocorrencia = OcorrenciaEntrega.objects.create(
            pedido=pedido,
            entregador=entregador,
            tipo=serializer.validated_data['tipo'],
            descricao=serializer.validated_data['descricao']
        )
        
        # TODO: Notificar lojista sobre a ocorrência
        
        return Response({
            'sucesso': 'Ocorrência registrada com sucesso!',
            'ocorrencia': OcorrenciaEntregaSerializer(ocorrencia).data
        })


class EntregadorViewSet(viewsets.ModelViewSet):
    serializer_class = EntregadorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.tipo_usuario == 'entregador':
            # Entregador vê apenas seu próprio perfil
            try:
                return Entregador.objects.filter(usuario=user)
            except Entregador.DoesNotExist:
                return Entregador.objects.none()
                
        elif user.tipo_usuario in ['lojista', 'superadmin']:
            # Lojista e superadmin veem todos os entregadores
            return Entregador.objects.all()
            
        else:
            return Entregador.objects.none()

    @action(detail=False, methods=['get'], permission_classes=[IsLojistaOrSuperAdmin])
    def disponiveis(self, request):
        """Lista entregadores disponíveis"""
        entregadores = Entregador.objects.filter(
            disponivel=True,
            em_pausa=False
        ).order_by('-nota_media')
        
        serializer = self.get_serializer(entregadores, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def alterar_disponibilidade(self, request, pk=None):
        """Entregador altera sua disponibilidade"""
        entregador = self.get_object()
        
        # Verificar se é o próprio entregador
        if request.user.entregador != entregador:
            return Response(
                {'erro': 'Você só pode alterar sua própria disponibilidade.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        disponivel = request.data.get('disponivel')
        em_pausa = request.data.get('em_pausa')
        
        if disponivel is not None:
            entregador.disponivel = disponivel
        if em_pausa is not None:
            entregador.em_pausa = em_pausa
            
        entregador.save()
        
        return Response({
            'sucesso': 'Disponibilidade alterada com sucesso!',
            'entregador': self.get_serializer(entregador).data
        })


class AvaliacaoEntregadorViewSet(viewsets.ModelViewSet):
    serializer_class = AvaliacaoEntregadorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.tipo_usuario == 'entregador':
            # Entregador vê suas avaliações
            try:
                return AvaliacaoEntregador.objects.filter(entregador__usuario=user)
            except:
                return AvaliacaoEntregador.objects.none()
                
        elif user.tipo_usuario in ['lojista', 'superadmin']:
            # Lojista vê avaliações dos entregadores
            return AvaliacaoEntregador.objects.all()
            
        else:
            # Cliente vê avaliações que fez
            return AvaliacaoEntregador.objects.filter(pedido__cliente=user)

    def perform_create(self, serializer):
        # Validar se o cliente pode avaliar este pedido/entregador
        pedido = serializer.validated_data['pedido']
        if pedido.cliente != self.request.user:
            raise ValueError("Você só pode avaliar entregas dos seus próprios pedidos.")
        
        if pedido.status != 'entregue':
            raise ValueError("Só é possível avaliar entregas concluídas.")
        
        serializer.save()


class OcorrenciaEntregaViewSet(viewsets.ModelViewSet):
    serializer_class = OcorrenciaEntregaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.tipo_usuario == 'entregador':
            # Entregador vê suas ocorrências
            try:
                return OcorrenciaEntrega.objects.filter(entregador__usuario=user)
            except:
                return OcorrenciaEntrega.objects.none()
                
        elif user.tipo_usuario in ['lojista', 'superadmin']:
            # Lojista vê todas as ocorrências
            return OcorrenciaEntrega.objects.all()
            
        else:
            return OcorrenciaEntrega.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[IsLojistaOrSuperAdmin])
    def resolver(self, request, pk=None):
        """Marca ocorrência como resolvida"""
        ocorrencia = self.get_object()
        observacoes_resolucao = request.data.get('observacoes_resolucao', '')
        
        ocorrencia.resolvido = True
        ocorrencia.observacoes_resolucao = observacoes_resolucao
        ocorrencia.save()
        
        return Response({
            'sucesso': 'Ocorrência marcada como resolvida!',
            'ocorrencia': self.get_serializer(ocorrencia).data
        })