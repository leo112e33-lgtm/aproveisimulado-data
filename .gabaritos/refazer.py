"""
Refaz as 10 explicacoes corrigidas com base nas imagens das provas oficiais
inspecionadas em .provas/imagens/.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NOVAS_EXPLICACOES = [
    (2018, 1, 15, "D",
     "**Por que a alternativa D esta correta:** O poema 'Dia 20/10' de Torquato Neto repete obsessivamente 'E preciso nao morrer por enquanto', 'enquanto e tempo nao morrer na via publica', 'sobreviver para verificar'. Esse fluxo de afirmativas defensivas projeta a consciencia da agonia antecipada — o sujeito poetico antev a propria morte e tenta adia-la, num discurso obsessivo de auto-preservacao.\n\n**Conceito-chave:** Poesia marginal brasileira — Torquato Neto (1944-1972) suicidou-se aos 28 anos um dia apos escrever este poema; a obra antecipa liricamente o desfecho tragico, marca da geracao tropicalista-marginal."),

    (2021, 1, 15, "D",
     "**Por que a alternativa D esta correta:** O conto 'Um homem celebre' de Machado de Assis retrata o personagem Pestana, compositor que aspira a ser erudito (referencias a Mozart) mas se rende a polcas/maxixes populares — generos associados historicamente a escravidao e a mesticagem. Esse conflito interno representa a tensa relacao entre o erudito e o popular na constituicao da musica brasileira: a alta cultura desejada vs. o gosto popular que efetivamente impulsiona o sucesso.\n\n**Conceito-chave:** Cultura erudita vs. popular no Brasil — Machado anteviu no seculo XIX o dilema central da identidade musical brasileira; tema retomado no Modernismo e consolidado com Villa-Lobos."),

    (2021, 1, 25, "B",
     "**Por que a alternativa B esta correta:** O delegado mistura linguagem rebuscada ('dura lex', 'autoridades constituidas') com gírias ('em cana', 'morou?', 'gringos'), criando uma figura caricata. O ponto comico vem quando ele descobre que a mulher e parente de militares de alta patente — encolhe imediatamente ('Estaressudo... — Da alva, minha senhora?'). Esse desfecho confere a narrativa um tom anedotico: a autoridade aparente desmonta-se como anedota.\n\n**Conceito-chave:** Anedota literaria (Fernando Sabino, 'A mulher do vizinho') — narrativa breve que ridiculariza autoridades pelo contraste entre pose e realidade; recurso classico da cronica brasileira."),

    (2021, 1, 38, "C",
     "**Por que a alternativa C esta correta:** O eu lirico do poema de Hilda Hilst pede ao outro 'manda-me dizer' ('e lua cheia', 'e lua nova') e evoca lembrancas concretas — 'brilho das mares', 'peixes rosados', 'meus pes molhados'. Essas imagens da memoria sustentam o desejo do reencontro pleno ('revestida de luz te volto a ver') — o sonho de autorrealizacao desenhado pela memoria.\n\n**Conceito-chave:** Lirica amorosa contemporanea de Hilda Hilst — memoria afetiva como forca propulsora do desejo; a plenitude se constroi pela evocacao de momentos passados, projetada como reencontro futuro."),

    (2021, 1, 53, "B",
     "**Por que a alternativa B esta correta:** Ze de Sila relata pratica da avo paraibana: emborcar pratos no terreiro e rezar para sustentar a chuva — costume da cultura sertaneja. O texto destaca essa pratica como exemplo de praticas misticas associadas a patrimonio cultural — religiosidade popular e saber da terra constituem patrimonio imaterial regional.\n\n**Conceito-chave:** Patrimonio imaterial brasileiro — saberes, ritos e tradicoes (como simpatias para chuva) sao reconhecidos pelo IPHAN como bens culturais; tipico do sertao nordestino."),

    (2021, 2, 49, "E",
     "**Por que a alternativa E esta correta:** Calcula-se a media de vendas por franquia para cada um dos cinco lanches (somando vendas das tres franquias e dividindo por 3). O lanche tipo V apresenta a maior media entre os cinco — por isso a gerencia o inclui definitivamente no cardapio.\n\n**Conceito-chave:** Media aritmetica simples — Σxi/n; usada em decisoes baseadas em desempenho medio entre unidades comparaveis."),

    (2021, 2, 55, "C",
     "**Por que a alternativa C esta correta:** Sistema de media ponderada: o tempo medio total e 6 min, com tres faixas etarias contribuindo com seus tempos medios (3, 5 e 12 min) ponderados pelos percentuais. Resolvendo 3·x + 5·(100-x-y) + 12·y = 600 com x e y sendo os percentuais das faixas extremas, obtem-se x=20% (10-24 anos) e y=60% (24-60 anos), com 20% restantes na faixa 60+. Verificacao: 3·20 + 5·60 + 12·20 = 600 → media 6 min ✓.\n\n**Conceito-chave:** Media ponderada — Σ(xi·pi)/Σpi; sistemas lineares para inferir distribuicoes a partir da media."),

    (2021, 2, 62, "E",
     "**Por que a alternativa E esta correta:** Com b=1, a△1 = a²+a-1 e 1△a = 1+a-a². Aplicando a operacao estrela, (a△1)*(1△a) = (a²+a-1)·(2+a-a²) = 0. Raizes: a²+a-1=0 da a=(-1±√5)/2; e 2+a-a²=0 (ou a²-a-2=0) da a=2 ou a=-1. As duas maiores raizes sao 2 e (-1+√5)/2; sua soma e (3+√5)/2 — valor recebido pelo navio receptor.\n\n**Conceito-chave:** Operacoes definidas e equacoes do segundo grau — fatoracao da composicao para evitar grau 3; soma de raizes pelo Teorema de Girard ou diretamente pela formula de Bhaskara."),

    (2022, 2, 53, "D",
     "**Por que a alternativa D esta correta:** No cubo da Figura 2, tres quadrados cinza ocupam um quarto de tres faces adjacentes a um vertice comum. Na planificacao em cruz da Figura 1, ao desdobrar essas tres faces, os quadrados pintados precisam aparecer no canto comum a elas — nas posicoes correspondentes do mesmo vertice apos o desdobramento. So a alternativa D respeita essa posicao relativa preservada.\n\n**Conceito-chave:** Planificacao de poliedros — adjacencia de faces e posicao de vertices comuns sao mantidas no desdobramento; visualizacao espacial fundamental em geometria."),

    (2023, 2, 89, "C",
     "**Por que a alternativa C esta correta:** Aquecimento global tem efeito desigual: os polos se aquecem 2-4 vezes mais rapido que a media global (amplificacao polar). Como o inverno polar se aquece mais que o verao polar, a amplitude termica anual diminui — caracterizando a diminuicao da variacao de temperatura nas regioes polares do planeta.\n\n**Conceito-chave:** Amplificacao artica/polar — efeito-albedo (gelo derretido absorve mais calor), feedback positivo, transporte de calor oceanico-atmosferico fazem polos serem epicentro do aquecimento global."),
]

def main():
    cnt = 0
    for ano, dia, num, letra, expl in NOVAS_EXPLICACOES:
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
    print(f"\nTotal refeitos: {cnt}")

if __name__ == "__main__":
    main()
