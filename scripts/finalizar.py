# -*- coding: utf-8 -*-
"""Aplica os conceitos-chave escritos a mao e corrige rotulos/typo."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

CONCEITOS = {
 "2023_1_1": "Interpretacao e dialogo entre textos: a partir de textos de uma mesma tematica (o cartaz e a sinopse do filme), identificar a ideia central que os articula — aqui, a de que um olhar atento e diferenciado para o outro e capaz de gerar mudancas.",
 "2023_1_5": "Funcao social da linguagem: reconhecer o engajamento do texto artistico como instrumento de denuncia e repudio diante de um problema social — neste caso, a violencia e a xenofobia.",
 "2023_1_7": "Construcao da identidade no texto literario: analisar como os recursos descritivos do corpo sao usados pela narradora para afirmar uma autoimagem que desafia os padroes esteticos impostos.",
 "2023_1_10": "Relacao entre linguagem e tecnologia: perceber como a analise de marcas linguisticas (como a pobreza vocabular) serve para identificar padroes de comportamento e a disseminacao de informacoes inveridicas por perfis falsos.",
 "2023_1_25": "Linguagem figurada (metafora): interpretar como a comparacao entre o arado e a palavra constroi uma reflexao sobre a propria linguagem e sobre a (in)comunicacao quando ela falha em seu proposito.",
 "2023_1_26": "Interpretacao textual e projecao temporal no discurso: identificar como o autor antecipa um cenario futuro — o apagamento das marcas da escravidao no convivio social — para enfatizar suas mazelas.",
 "2023_1_29": "Recursos de construcao de sentido (contraste e ironia): perceber como a justaposicao entre o sublime (o ideal historico) e o grotesco (a imagem repugnante dos ratos) produz o efeito desconcertante do texto.",
 "2023_1_30": "Linguagem literaria e contexto historico: realizar a leitura alegorica de um texto ficcional, relacionando a 'Companhia' e seu culto ao medo ao autoritarismo da Ditadura Militar brasileira.",
 "2023_1_31": "Analise do eu lirico e do contraste: compreender como a banalidade do cotidiano (as migalhas, o bule de cafe) e usada para diluir e conter a comocao de um amor que se encerra.",
 "2023_1_32": "Hibridismo e dialogo cultural: identificar a inter-relacao entre referenciais esteticos aparentemente distantes (o erudito europeu e o popular nordestino) reunidos numa mesma performance.",
 "2023_1_34": "Relacao entre arte erudita e cultura popular: reconhecer a reelaboracao estetica — e nao a copia mimetica — de praticas religiosas afro-brasileiras transformadas em linguagem cenica.",
 "2023_1_35": "Leitura de texto informativo e inferencia: articular os dados apresentados (crescimento, popularidade, reconhecimento institucional) para concluir que ha uma condicao favoravel a expansao da modalidade.",
 "2023_1_36": "Memoria e ressignificacao cultural: entender como praticas culturais, como o Marabaixo, transformam um episodio dramatico (a morte de escravizados) em uma expressao cultural viva e festiva.",
 "2023_1_37": "Relacao entre arte e tecnologias digitais: compreender as redes sociais como vitrine que amplia a circulacao e a visibilidade internacional da producao artistica.",
 "2023_1_41": "Esporte e saude mental: fazer a leitura critica de uma noticia que desloca o foco do desempenho para a dimensao emocional e psicologica dos atletas.",
 "2023_1_42": "Determinantes sociais da atividade fisica: identificar a desigualdade entre classes sociais como fator central no acesso desigual as praticas corporais de lazer.",
 "2023_1_53": "Tectonica de placas: reconhecer que grandes cordilheiras, como o Himalaia, se formam e continuam crescendo pelo encontro (colisao) de placas tectonicas continentais, gerando dobramentos.",
 "2023_1_57": "Filosofia e etica do perdao: compreender, no texto de Ricoeur, o perdao como ato livre e soberano que expressa a autonomia do individuo, podendo inclusive ser recusado.",
 "2023_1_59": "Processo civilizador (sociologia de Norbert Elias): entender a etiqueta a mesa, como o uso do garfo, enquanto marca de distincao entre as classes sociais.",
}

def append_conceito(exp, texto):
    if "Conceito-chave" in exp:
        return exp
    return exp.rstrip() + "\n\n**Conceito-chave:** " + texto

def main():
    falta = json.loads((ROOT/"scripts"/"falta.json").read_text())
    por_arq = {}
    for ano,dia,num in falta:
        por_arq.setdefault((ano,dia),[]).append(num)
    for (ano,dia),nums in por_arq.items():
        arq = ROOT/"enem"/str(ano)/f"dia{dia}.json"
        payload = json.loads(arq.read_text(encoding="utf-8"))
        idx = {q["numero"]:q for q in payload["questoes"]}
        for num in nums:
            q = idx[num]; k=f"{ano}_{dia}_{num}"
            exp = q.get("explicacao","") or ""
            if k in CONCEITOS:
                exp = append_conceito(exp, CONCEITOS[k])
            if k == "2020_2_54":
                exp = exp.replace("**3. O conceito-chave que o aluno precisa dominar:**", "**Conceito-chave:**")
            if k == "2023_2_39":
                exp = exp.replace("Conceept-chave", "Conceito-chave").replace("Conceept", "Conceito")
            q["explicacao"] = exp
        arq.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("finalizar: aplicado.")

if __name__ == "__main__":
    main()
