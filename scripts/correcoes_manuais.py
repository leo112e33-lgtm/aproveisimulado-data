"""
Correcoes manuais para questoes em que a API enem.dev retorna 404, dados
incorretos ou imagem quebrada. Ported de CorrecoesEnem.java do app Android.

Cada correcao e identificada pela tupla (ano, dia, num_questao).

As imagens referenciadas em "imagem_principal_local" / "imagens_alternativas_local"
estao no diretorio app/src/main/res/drawable/ do projeto Android. O script
01_baixar_questoes.py copia essas imagens para enem/<ano>/img/ no dataset.
"""

# Caminho do projeto Android (para copiar drawables locais).
ANDROID_DRAWABLE_DIR = (
    r"C:\Users\leo11\AndroidStudioProjects\AproveiSimulado2"
    r"\app\src\main\res\drawable"
)

# Cada entrada e uma "questao" pronta no mesmo formato que sai do
# 01_baixar_questoes.py. Campos com prefixo "_local_" referem-se a arquivos
# que precisam ser copiados do drawable do app.
CORRECOES = [
    # ENEM 2023 - DIA 1 - Questao 34
    {
        "ano": 2023, "dia": 1, "numero": 34,
        "titulo": "Questao 34 - ENEM 2023",
        "enunciado": (
            "TEXTO I\n\n"
            "Logo no inicio de Gira, um grupo de sete bailarinas ocupa o centro da cena. "
            "Maos cruzadas sobre a lateral esquerda do quadril, olhos fechados, troncos que "
            "pendulam sobre si mesmos em vaguissimas orbitas, tudo nelas sugere o transe. "
            "Esta estabelecido o carater volatil do que se passara no palco dali para frente. "
            "Mas engana-se quem pensa que vai assistir a uma representacao mimetica dos cultos afro-brasileiros.\n\n"
            "TEXTO II"
        ),
        "_local_imagem_principal": "enem2023_q34_bailarinas.png",
        "alternativas_introducao": (
            "No dialogo que estabelece com religioes afro-brasileiras, "
            "sintetizado na descricao e na imagem do espetaculo, a danca exprime uma"
        ),
        "alternativas": [
            "A) critica aos movimentos padronizados do bale classico.",
            "B) representacao contemporanea de rituais ancestrais extintos.",
            "C) reelaboracao estetica erudita de praticas religiosas populares.",
            "D) releitura ironica da atmosfera mistica presente no culto a entidades.",
            "E) oposicao entre o resgate de tradicoes e a efemeridade da vida humana.",
        ],
        "imagens_alternativas": [None] * 5,
        "correta": "C",
    },
    # ENEM 2023 - DIA 1 - Questao 44
    {
        "ano": 2023, "dia": 1, "numero": 44,
        "titulo": "Questao 44 - ENEM 2023",
        "enunciado": "",
        "_local_imagem_principal": "enem2023_q44_amamentacao.png",
        "alternativas_introducao": "Essa campanha publicitaria do Ministerio da Saude visa",
        "alternativas": [
            "A) divulgar um conjunto de beneficios proporcionados pela amamentacao.",
            "B) apresentar tratamentos para infeccoes respiratorias em bebes.",
            "C) defender o direito das mulheres de amamentar em publico.",
            "D) orientar sobre os exercicios para uma boa amamentacao.",
            "E) informar sobre o aumento de anticorpos nas maes.",
        ],
        "imagens_alternativas": [None] * 5,
        "correta": "A",
    },
    # ENEM 2023 - DIA 1 - Questao 56
    {
        "ano": 2023, "dia": 1, "numero": 56,
        "titulo": "Questao 56 - ENEM 2023",
        "enunciado": "",
        "_local_imagem_principal": "enem2023_q56_charge.png",
        "alternativas_introducao": (
            "A charge ilustra um anseio presente na sociedade contemporanea, "
            "que se caracteriza pela"
        ),
        "alternativas": [
            "A) situacao de revolta individual.",
            "B) satisfacao de desejos pessoais.",
            "C) participacao em acoes decisorias.",
            "D) permanencia em passividade social.",
            "E) convivencia em interesses partidarios.",
        ],
        "imagens_alternativas": [None] * 5,
        "correta": "C",
    },
    # ENEM 2023 - DIA 2 - Questao 89
    {
        "ano": 2023, "dia": 2, "numero": 89,
        "titulo": "Questao 89 - ENEM 2023",
        "enunciado": "",
        "_local_imagem_principal": "enem2023_q89_mapa.png",
        "alternativas_introducao": (
            "Com base nas informacoes dos mapas e nos conhecimentos sobre as "
            "mudancas climaticas globais, conclui-se que o aumento da "
            "temperatura media global de 4 graus C em relacao ao periodo "
            "pre-industrial causaria"
        ),
        "alternativas": [
            "A) reducao das chuvas em todas as regioes tropicais do planeta.",
            "B) aquecimento uniforme de todas as regioes terrestres do planeta.",
            "C) diminuicao da variacao de temperatura nas regioes polares do planeta.",
            "D) intensificacao dos contrastes climaticos entre as regioes do planeta.",
            "E) homogeneizacao da distribuicao das chuvas nas regioes temperadas do planeta.",
        ],
        "imagens_alternativas": [None] * 5,
        "correta": "D",
    },
    # ENEM 2023 - DIA 2 - Questao 132
    {
        "ano": 2023, "dia": 2, "numero": 132,
        "titulo": "Questao 132 - ENEM 2023",
        "enunciado": (
            "O manual de um automovel alerta sobre os cuidados em relacao a "
            "pressao do ar no interior dos pneus. Recomenda-se que a pressao "
            "seja verificada com os pneus frios (a temperatura ambiente). "
            "Um motorista, desatento a essa informacao, realizou uma viagem "
            "longa sobre o asfalto quente e, em seguida, verificou que a "
            "pressao P_0 no interior dos pneus nao era a recomendada pelo "
            "fabricante. Na ocasiao, a temperatura dos pneus era T_0. "
            "Apos um longo periodo em repouso, os pneus do carro atingiram "
            "a temperatura ambiente T. Durante o resfriamento, nao ha "
            "alteracao no volume dos pneus e na quantidade de ar no seu "
            "interior. Considere o ar dos pneus um gas perfeito (tambem "
            "denominado gas ideal). Durante o processo de resfriamento, os "
            "valores de pressao em relacao a temperatura (P x T) sao "
            "representados pelo grafico:"
        ),
        "alternativas_introducao": "",
        "alternativas": ["A)", "B)", "C)", "D)", "E)"],
        "_local_imagens_alternativas": [
            "enem2023_q132_alt_a.png",
            "enem2023_q132_alt_b.png",
            "enem2023_q132_alt_c.png",
            "enem2023_q132_alt_d.png",
            "enem2023_q132_alt_e.png",
        ],
        "correta": "E",
    },
]


def chave(ano: int, dia: int, numero: int) -> str:
    return f"{ano}_{dia}_{numero}"


CORRECOES_POR_CHAVE = {chave(c["ano"], c["dia"], c["numero"]): c for c in CORRECOES}


def obter(ano: int, dia: int, numero: int):
    return CORRECOES_POR_CHAVE.get(chave(ano, dia, numero))
