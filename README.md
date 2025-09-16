# Menuly Delivery

Sistema completo de delivery white-label para restaurantes, pizzarias e lanchonetes.

## Visão Geral
- Plataforma web responsiva para clientes, lojistas e entregadores
- Gestão de pedidos, entregadores, cardápio, clientes e relatórios
- Painel do lojista com dashboard, notificações e controle de entregas
- Painel do entregador (motoboy) para aceitar e gerenciar entregas
- Integração com meios de pagamento (Pix, cartão)
- Sistema de avaliação, ocorrências e histórico de entregas

## Principais Funcionalidades
- Cadastro e gestão de produtos, categorias e adicionais
- Checkout rápido, cálculo de frete e busca por CEP
- Acompanhamento de pedidos em tempo real
- Gestão de entregadores: status, avaliação, ocorrências
- Relatórios de vendas, entregas e desempenho
- Suporte a múltiplos planos para lojistas
- Notificações (web, WhatsApp, e-mail)

## Tecnologias
- Backend: Django 4/5, Django REST Framework
- Frontend: HTML5, Bootstrap 5, JavaScript
- Banco de Dados: SQLite (padrão), suporte a PostgreSQL/MySQL
- Integração: APIs RESTful, Webhooks

## Como rodar localmente
```bash
# Clone o repositório
git clone https://github.com/ronwsv/Menuly_delivery.git
cd Menuly_delivery

# Crie e ative um ambiente virtual (opcional)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instale as dependências
pip install -r requirements.txt

# Execute as migrações
python manage.py migrate

# Crie um superusuário
python manage.py createsuperuser

# Rode o servidor
python manage.py runserver
```

Acesse: http://127.0.0.1:8000/

## Estrutura de Pastas
- `core/` - app principal (pedidos, clientes, planos)
- `loja/` - frontend do cliente
- `admin_loja/` - painel do lojista
- `entregadores/` - painel e API dos entregadores
- `painel_entregador/` - painel web/app para motoboys
- `templates/` - templates HTML
- `static/` - arquivos estáticos (css, js, imagens)

## Contribuição
Pull requests são bem-vindos! Para grandes mudanças, abra uma issue primeiro para discutir o que você gostaria de modificar.

## Licença
[MIT](LICENSE)



[criei uma loja de teste meninas
	{
		"nome": "Ayla Renata Gonçalves",
		"idade": 27,
		"cpf": "940.810.968-64",
		"rg": "29.939.701-4",
		"data_nasc": "26/01/1998",
		"sexo": "Feminino",
		"signo": "Aquário",
		"mae": "Camila Daniela Rafaela",
		"pai": "Pedro Henrique Cláudio Gonçalves",
		"email": "ayla-goncalves92@megasurgical.com.br",
		"senha": "XGaFfCMbA9",
		"cep": "07025-120",
		"endereco": "Rua Dona Leopoldina",
		"numero": 960,
		"bairro": "Vila Augusta",
		"cidade": "Guarulhos",
		"estado": "SP",
		"telefone_fixo": "(11) 3753-2178",
		"celular": "(11) 98382-2768",
		"altura": "1,51",
		"peso": 82,
		"tipo_sanguineo": "B-",
		"cor": "laranja"
	}
]
