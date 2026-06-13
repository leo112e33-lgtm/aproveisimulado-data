# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

TEXTOS = {
 ("2020",2,54):
  "**Por que a alternativa B está correta:** A torneira goteja 5 gotas por segundo, e cada gota tem 5 × 10⁻² mL, "
  "logo a vazão é 5 × 0,05 = 0,25 mL/s. Como o balde de 18 L está com 50% da capacidade, faltam 9 L (9000 mL) para enchê-lo. "
  "O tempo necessário é 9000 ÷ 0,25 = 36000 s, que equivalem a 36000 ÷ 3600 = 10 horas.\n\n"
  "**Conceito-chave:** Vazão e conversão de unidades — calcular o volume escoado por unidade de tempo e converter "
  "corretamente entre mililitros/litros e segundos/horas para obter o tempo total.",

 ("2020",2,78):
  "**Por que a alternativa A está correta:** A base do recipiente mede 4 cm por 3 cm, portanto sua área é 4 × 3 = 12 cm². "
  "Para a água subir de 8 cm até 15 cm é preciso elevar a coluna em 7 cm, o que corresponde a um volume de 12 × 7 = 84 cm³. "
  "Como cada bolinha submersa ocupa (e desloca) 6 cm³ de água, o número mínimo de bolinhas é 84 ÷ 6 = 14.\n\n"
  "**Conceito-chave:** Volume de prisma e deslocamento de líquidos — o volume de água deslocado é igual ao volume dos "
  "corpos submersos; calcula-se a variação de volume (área da base × variação de altura) e divide-se pelo volume de cada objeto.",

 ("2023",2,84):
  "**Por que a alternativa E está correta:** A pessoa parte da posição da estrela, voltada para o norte, e sobe mais "
  "quatro fileiras nessa direção, chegando à fileira I. Em seguida, olhando para a sua direita (leste), conta até a "
  "terceira poltrona, que é a de número 6. Logo, a poltrona é identificada por I6.\n\n"
  "**Conceito-chave:** Localização por coordenadas e orientação espacial — usar a referência de fileiras (letras) e "
  "posições (números), junto com os pontos cardeais e as noções de esquerda/direita, para localizar um ponto no plano.",
}

for (ano,dia,num),texto in TEXTOS.items():
    arq = ROOT/"enem"/ano/f"dia{dia}.json"
    payload = json.loads(arq.read_text(encoding="utf-8"))
    for q in payload["questoes"]:
        if q.get("numero")==num:
            q["explicacao"]=texto
            break
    arq.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ok", ano, dia, num)
