from django.core.management.base import BaseCommand
from core.models import Produto, Categoria, OpcaoPersonalizacao, ItemPersonalizacao
from django.db import transaction

class Command(BaseCommand):
    help = 'Adiciona a opção "Meia Pizza" (com itens Inteira e Meia) para todos os produtos da categoria Pizzas.'

    def handle(self, *args, **options):
        categoria_nome = 'Pizzas'  # Altere aqui se o nome da categoria for diferente
        opcao_nome = 'Meia Pizza'
        itens = [
            {'nome': 'Inteira', 'preco_adicional': 0.00},
            {'nome': 'Meia', 'preco_adicional': 0.00},
        ]
        try:
            categoria = Categoria.objects.get(nome__iexact=categoria_nome)
        except Categoria.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Categoria "{categoria_nome}" não encontrada.'))
            return
        produtos = Produto.objects.filter(categoria=categoria)
        count = 0
        with transaction.atomic():
            for produto in produtos:
                if OpcaoPersonalizacao.objects.filter(produto=produto, nome__iexact=opcao_nome).exists():
                    self.stdout.write(f'Produto "{produto.nome}" já possui a opção "{opcao_nome}".')
                    continue
                opcao = OpcaoPersonalizacao.objects.create(
                    produto=produto,
                    nome=opcao_nome,
                    tipo='radio',
                    obrigatorio=True,
                    ordem=99,
                    ativo=True
                )
                for idx, item in enumerate(itens):
                    ItemPersonalizacao.objects.create(
                        opcao=opcao,
                        nome=item['nome'],
                        preco_adicional=item['preco_adicional'],
                        ordem=idx,
                        ativo=True
                    )
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Opção "{opcao_nome}" adicionada ao produto "{produto.nome}".'))
        self.stdout.write(self.style.SUCCESS(f'Processo concluído. {count} produtos atualizados.'))
