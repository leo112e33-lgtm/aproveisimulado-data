# -*- coding: utf-8 -*-
"""Corrige grupos da UNESP 2023 cujo texto-base compartilhado nao foi anexado.
Q09-12 dividem o soneto de Gregorio de Matos; Q21-26 dividem o grafico+mapa+texto
(Antartica/Concordia, The Economist). Texto-base extraido do PDF oficial.
Idempotente: nao reaplica se o base ja estiver presente."""
import json, os

DIR = os.path.join(os.path.dirname(__file__), "..", "vestibular", "unesp")
PATH = os.path.join(DIR, "2023.json")

SONETO = (
    "Leia o soneto “Descreve o que era naquele tempo a cidade da Bahia”, "
    "do poeta Gregório de Matos (1636-1696), para responder às questões de 09 a 12.\n\n"
    "A cada canto um grande conselheiro,\n"
    "Que nos quer governar cabana e vinha;\n"
    "Não sabem governar sua cozinha,\n"
    "E podem governar o mundo inteiro.\n\n"
    "Em cada porta um bem frequente olheiro,\n"
    "Que a vida do vizinho e da vizinha\n"
    "Pesquisa, escuta, espreita e esquadrinha,\n"
    "Para o levar à praça e ao terreiro.\n\n"
    "Muitos mulatos desavergonhados,\n"
    "Trazidos sob os pés os homens nobres¹,\n"
    "Posta nas palmas toda a picardia,\n\n"
    "Estupendas usuras nos mercados,\n"
    "Todos os que não furtam muito pobres:\n"
    "E eis aqui a cidade da Bahia.\n\n"
    "(Gregório de Matos. Poemas escolhidos, 2010.)\n"
    "¹ Trazidos sob os pés os homens nobres: na visão de Gregório de Matos, "
    "os mulatos em ascensão subjugam com esperteza os verdadeiros “homens nobres”."
)

ANTARTICA = (
    "Examine o gráfico e o mapa e leia o texto para responder às questões de 21 a 26.\n\n"
    "In March 2022, parts of Antarctica have been 40 °C warmer than their March average\n\n"
    "![](vestibular/unesp/img/2023_base21_fig1.png)\n\n"
    "The Concordia research station is one of the most inhospitable places on Earth. "
    "At 3,000 m above sea level on the Antarctic Plateau, the temperature rarely rises "
    "above -25 °C even in the summer. In midwinter it can fall to around -80 °C. "
    "The air is painfully dry, and fingers, toes and noses can freeze in minutes. "
    "The dozen or so crew, mainly French and Italian, who live and work in the station "
    "would normally venture out only for essential work. But Concordia has recently "
    "experienced a heatwave. On March 18th the temperature reached a high of -11.8 °C "
    "— more than 40 °C warmer than the average for this time of year.\n\n"
    "Similarly freakish weather was recorded across eastern Antarctica. Temperatures at "
    "the Russian-run Vostok research station rose to -17.7 °C, more than 15 °C above "
    "the previous record for March, set in 1967. Across the continent temperatures were "
    "4.5 °C higher than usual (though in recent days they have returned to a normal range).\n\n"
    "Meteorologists have attributed the latest heatwave to an atmospheric “river” of "
    "warm, damp air blowing towards Antarctica from the Southern Ocean near Australia. "
    "It is difficult to know whether climate change is to blame for one-off weather events. "
    "But over the past 65 years or so there has been an increase in the number of "
    "“high temperature” days at Antarctic stations.\n\n"
    "Most regions of Antarctica have been spared global warming. In the late 20th century, "
    "a large hole opened up in the ozone layer above the South Pole. This has a regional "
    "cooling effect, which has offset much of the heating caused by rising concentrations "
    "of greenhouse gases in the atmosphere. Temperatures on the continent rarely climb "
    "above freezing, which preserves its vast ice sheets (although rising sea temperatures "
    "do threaten some areas). Even in the recent surge, temperatures stayed well below zero.\n\n"
    "(www.economist.com, 24.03.2022. Adaptado.)"
)

GRUPOS = [
    (range(9, 13), SONETO, "A cada canto um grande conselheiro"),
    (range(21, 27), ANTARTICA, "Concordia research station"),
]

def main():
    d = json.load(open(PATH, encoding="utf-8"))
    qs = {q["numero"]: q for q in d["questoes"]}
    mudou = 0
    for nums, base, marcador in GRUPOS:
        for n in nums:
            q = qs.get(n)
            if not q:
                print(f"  AVISO: Q{n} nao encontrada")
                continue
            enun = q.get("enunciado", "")
            if marcador in enun:
                print(f"  Q{n}: base ja presente, pulando")
                continue
            q["enunciado"] = base + "\n\n" + enun.strip()
            mudou += 1
            print(f"  Q{n}: base anexada (+{len(base)} chars)")
    json.dump(d, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"=== {mudou} questoes atualizadas ===")

if __name__ == "__main__":
    main()
