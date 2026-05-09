"""
Corrige gabaritos divergentes em relacao ao INEP oficial caderno azul.
Atualiza tanto 'correta' quanto 'explicacao' das questoes afetadas.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CORRECOES = [
    # (ano, dia, numero, letra_correta_inep, nova_explicacao)
    (2018, 1, 15, "D",
     "**Por que a alternativa D esta correta:** Torquato Neto repete 'E preciso nao morrer por enquanto', 'enquanto e tempo nao morrer na via publica'. O texto e a vespera do suicidio do poeta — repercute a consciencia da agonia antecipada, a percepcao da morte iminente que o sujeito tenta adiar.\n\n**Conceito-chave:** Poesia marginal e tropicalismo — Torquato Neto suicidou-se em 1972 aos 28 anos; o poema 'Dia 20/10' antecipa lirica e dramaticamente a propria morte."),
    (2021, 1, 15, "D",
     "**Por que a alternativa D esta correta:** Machado descreve compositor erudito (referencias a Mozart) que se rende ao maxixe popular. A obra explicita a tensa relacao entre o erudito e o popular na constituicao da musica brasileira — choque entre a formacao classica e os generos urbanos populares no fim do seculo XIX.\n\n**Conceito-chave:** Modernismo musical brasileiro — maxixe, polca, samba; Machado de Assis ja antecipava o dialogo entre alta cultura e cultura popular na configuracao da identidade musical do pais."),
    (2021, 1, 25, "B",
     "**Por que a alternativa B esta correta:** O delegado usa expressoes pomposas misturadas a giria ('dura lex', 'morou?', 'em cana'), tratando os 'gringos' com autoritarismo caricato. Esse contraste linguistico confere a narrativa um tom anedotico — situacao comica que ridiculariza a propria figura do agente da autoridade.\n\n**Conceito-chave:** Anedota literaria — narrativa breve e comica que ironiza autoridades por meio do exagero e do contraste de registros; recurso classico da literatura brasileira de costumes."),
    (2021, 1, 38, "C",
     "**Por que a alternativa C esta correta:** O eu lirico recorda 'brilho das mares', 'peixes rosados', 'meus pes molhados' — imagens da memoria afetiva. O desejo expresso remete ao sonho de autorrealizacao desenhado pela memoria — o reencontro projetado a partir das lembrancas.\n\n**Conceito-chave:** Lirica amorosa contemporanea (Hilda Hilst) — memoria afetiva como motor do desejo; reencontro e plenitude buscados via reconstrucao do passado."),
    (2021, 1, 53, "B",
     "**Por que a alternativa B esta correta:** Ze de Sila relata pratica da avo (rezar e emborcar pratos para sustentar a chuva) — costume tradicional regional. O texto destaca praticas misticas associadas a patrimonio cultural — religiosidade popular como heranca cultural do sertao.\n\n**Conceito-chave:** Patrimonio imaterial — saberes, ritos e tradicoes populares constituem cultura brasileira; valorizados pelo IPHAN como patrimonio."),
    (2021, 2, 49, "E",
     "**Por que a alternativa E esta correta:** Calculando a media de vendas por franquia para cada tipo de lanche, o tipo V apresenta a maior media nas tres franquias. Por isso a gerencia o inclui no cardapio.\n\n**Conceito-chave:** Media aritmetica simples — soma dos valores dividida pelo numero de elementos; usada em decisoes baseadas em desempenho medio."),
    (2021, 2, 55, "C",
     "**Por que a alternativa C esta correta:** Sistema com media ponderada total = 6 min usando os percentuais x, y e o restante. Resolvendo as equacoes (3x + 5y + 12·resto)/100 = 6 e x+y+resto=100, obtem-se x=20% e y=60%.\n\n**Conceito-chave:** Media ponderada — Σ(xi·fi)/Σfi; sistemas de equacoes lineares para descobrir distribuicoes percentuais."),
    (2021, 2, 62, "E",
     "**Por que a alternativa E esta correta:** A equacao (a△b)*(b△a)=0 fatora-se de modo que (a△b)=0 ou (b△a)=0. Resolvendo as duas quadraticas e somando as duas maiores raizes, obtem-se o valor da alternativa E.\n\n**Conceito-chave:** Operacoes algebricas definidas e equacoes do segundo grau — composicao de operacoes nao-padrao; aplicacoes em sistemas de codificacao."),
    (2022, 2, 53, "D",
     "**Por que a alternativa D esta correta:** Os tres quadrados cinza tem um vertice em comum no cubo — cada quadrado ocupa um quarto da face e fica no canto adjacente ao vertice compartilhado. Na planificacao, esses quadrados aparecem nas posicoes correspondentes do canto comum, formando o padrao da alternativa D.\n\n**Conceito-chave:** Planificacao de poliedros — cada planificacao do cubo preserva relacoes de adjacencia; reconhecer faces vizinhas e essencial para visualizacao espacial."),
    (2023, 2, 89, "C",
     "**Por que a alternativa C esta correta:** Aquecimento global tem efeito amplificado nos polos (amplificacao artica): o inverno polar se aquece mais que o verao polar, reduzindo a amplitude termica anual. Por isso ocorre diminuicao da variacao de temperatura nas regioes polares.\n\n**Conceito-chave:** Amplificacao artica — efeito-albedo do gelo, intercambio oceanico e atmosferico fazem polos se aquecerem 2-4x mais rapido que media global."),
]

def main():
    cnt = 0
    for ano, dia, num, letra, expl in CORRECOES:
        arq = ROOT / "enem" / str(ano) / f"dia{dia}.json"
        d = json.loads(arq.read_text(encoding="utf-8"))
        for q in d["questoes"]:
            if q["numero"] == num:
                q["correta"] = letra
                q["explicacao"] = expl
                cnt += 1
                print(f"  {ano} d{dia} Q{num} -> {letra}")
                break
        arq.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTotal corrigidos: {cnt}")

if __name__ == "__main__":
    main()
