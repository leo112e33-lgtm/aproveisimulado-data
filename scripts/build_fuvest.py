# -*- coding: utf-8 -*-
import json, re, unicodedata
from pathlib import Path

BASE = Path(r"C:\Users\leo11\AndroidStudioProjects\aproveisimulado-data\vestibular\fuvest")
cand = {q["numero"]: q for q in json.loads((BASE / "_candidatas.json").read_text(encoding="utf-8"))}

SEL = [1, 22, 27, 30, 31, 41, 42, 46, 52, 55, 66, 84, 86, 87]

EXPL = {
 1: "**Resposta correta: D.** A interseccionalidade (Crenshaw) mostra como gênero e raça se somam; os dados do Dieese indicam que as mulheres negras ocupam as posições menos valorizadas e pior remuneradas do mercado de trabalho.\n\n**Conceito-chave:** Interseccionalidade — diferentes eixos de discriminação (gênero, raça, classe) se combinam e aprofundam as desigualdades.",
 22: "**Resposta correta: D.** É uma PA com a₁=120 e razão 6 (24 termos). A soma das 24 parcelas é S=(120+258)·24/2=4536. Como a 19ª parcela (a₁₉=120+18·6=228) não foi paga, Joana pagou 4536−228 = R$ 4.308,00.\n\n**Conceito-chave:** Progressão aritmética — aₙ=a₁+(n−1)r e Sₙ=(a₁+aₙ)·n/2.",
 27: "**Resposta correta: A.** As geadas em São Paulo concentram-se nas maiores altitudes (Serra da Mantiqueira), pois a altitude reduz a temperatura e favorece a perda de calor nas noites de inverno.\n\n**Conceito-chave:** Fatores climáticos — influência da altitude na temperatura e na formação de geadas.",
 30: "**Resposta correta: D.** Para Santo Agostinho, o tempo é medido na subjetividade. A passagem \"Mas no tempo não havia horas\" exprime a duração interior (tempo psicológico) no romance Angústia.\n\n**Conceito-chave:** Distinção entre tempo físico (objetivo) e tempo psicológico (subjetivo).",
 31: "**Resposta correta: C.** Para Hume, todas as ideias são cópias de impressões (sensações). Quem nunca experimentou o guaraná não pode ter a ideia do seu sabor, pois falta a impressão originária.\n\n**Conceito-chave:** Empirismo de Hume — as ideias derivam das impressões sensoriais.",
 41: "**Resposta correta: B.** O \"índio sacana\" designa um grupo social cuja inserção na sociedade equatoriana foi complexa e limitada, restrito a trabalhos subalternos e socialmente invisível.\n\n**Conceito-chave:** Interpretação de texto — identidade e marginalização social do indígena.",
 42: "**Resposta correta: C.** Na sociedade mineradora do século XVIII, os \"vadios\" eram tolerados pelas autoridades porque exerciam atividades complementares à mineração.\n\n**Conceito-chave:** Sociedade do ouro — trabalho avulso e controle social na Minas colonial.",
 46: "**Resposta correta: D.** Para Vernant, a pólis pressupõe a isonomia: a soberania circula entre os cidadãos e comandar/obedecer são termos reversíveis de uma mesma relação.\n\n**Conceito-chave:** Pólis grega — isonomia e participação política dos cidadãos.",
 52: "**Resposta correta: E.** A instabilidade no Sahel associa-se à escassez de recursos naturais, à diversidade étnica e aos resquícios da colonização (fronteiras artificiais e disputas de poder).\n\n**Conceito-chave:** Geopolítica africana — heranças coloniais e conflitos no Sahel.",
 55: "**Resposta correta: E.** A descrição da visão serve para sustentar a tese de que todos tendem ao saber, já que é a sensação que mais proporciona conhecimento.\n\n**Conceito-chave:** Estrutura argumentativa — a função de um exemplo na sustentação da tese (Aristóteles).",
 66: "**Resposta correta: A.** V=E·d=10⁴·100=10⁶ V; I=Q/t=30/10⁻³=3·10⁴ A; logo P=V·I=3·10¹⁰ W = 30 GW.\n\n**Conceito-chave:** Potência elétrica P=V·I, com V=E·d e I=Q/Δt.",
 84: "**Resposta correta: E.** Escolha por combinações: C(3,2)·C(8,6)=3·28=84 provas distintas.\n\n**Conceito-chave:** Análise combinatória — combinação simples C(n,p)=n!/[p!(n−p)!].",
 86: "**Resposta correta: B.** O volume da pedra é igual ao da água deslocada: área da base × variação da altura = π·8²·(23,5−20)=64π·3,5=224π cm³.\n\n**Conceito-chave:** Volume do cilindro e princípio do deslocamento de líquidos.",
 87: "**Resposta correta: C.** Primoriais: 2#=2, 3#=6, 5#=30, 7#=210, 11#=2310. O menor primorial maior que 2000 é 11# = 2310.\n\n**Conceito-chave:** Números primos e produto (primorial).",
}

def limpa(s):
    if s is None: return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("ଷ", "³").replace("ଶ", "²")
    s = re.sub(r"\s+", " ", s).strip()
    return s

questoes = []
for n in SEL:
    q = cand[n]
    enun = limpa(q["enun"])
    alts = []
    for letra in "ABCDE":
        t = limpa(q["alts"].get(letra, ""))
        # Q31: corta o vazamento do texto em ingles na alternativa E
        if n == 31 and letra == "E":
            t = t.split(" TEXTO PARA")[0].strip()
        alts.append(letra + ") " + t)
    questoes.append({
        "numero": n,
        "ano": 2023,
        "titulo": "Questão " + str(n) + " - FUVEST 2023",
        "enunciado": enun,
        "alternativas_introducao": "",
        "alternativas": alts,
        "imagens_alternativas": [None]*5,
        "imagem_principal": "",
        "imagens_extras": [],
        "correta": q["correta"],
        "explicacao": EXPL[n],
        "fonte": "fuvest_oficial",
        "fonte_url": "https://www.fuvest.br/wp-content/uploads/fuvest2023_primeira_fase_prova_V.pdf",
    })

payload = {
    "vestibular": "FUVEST",
    "ano": 2023,
    "titulo": "FUVEST 2023 — 1ª fase (seleção de questões)",
    "totalQuestoes": len(questoes),
    "observacao": "Seleção de questões reais da 1ª fase da FUVEST 2023 (Prova V), extraídas do PDF oficial. Questões que dependem de figuras/gráficos foram omitidas nesta versão.",
    "questoes": questoes,
}
(BASE / "2023.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("fuvest/2023.json gerado com", len(questoes), "questoes")
