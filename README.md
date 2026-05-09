# aproveisimulado-data

Dataset de questoes do ENEM (2018-2023) consumido pelo app **AproveiSimulado2**.

## Conteudo

```
enem/
  <ano>/
    dia1.json        # 90 questoes do dia 1
    dia2.json        # 90 questoes do dia 2
    img/             # imagens das questoes (compartilhadas pelos dois dias)
manifest.json        # indice de todas as provas disponiveis
```

## Estrutura de uma questao

```json
{
  "numero": 34,
  "ano": 2023,
  "dia": 1,
  "titulo": "Questao 34 - ENEM 2023",
  "enunciado": "TEXTO I\n\n...",
  "alternativasIntroducao": "No dialogo que estabelece com religioes...",
  "alternativas": [
    "A) ...",
    "B) ...",
    "C) ...",
    "D) ...",
    "E) ..."
  ],
  "imagensAlternativas": [null, null, null, null, null],
  "imagemPrincipal": "img/2023/q34_bailarinas.png",
  "imagensExtras": [],
  "correta": "C",
  "explicacao": "A alternativa C esta correta porque...",
  "fonteOriginal": "https://api.enem.dev/v1/exams/2023/questions/34",
  "fonteCorrecao": "manual"
}
```

## Pipeline de geração

```
01_baixar_questoes.py   ->  baixa da API enem.dev + correcoes manuais  ->  enem/<ano>/diaN.json
02_baixar_imagens.py    ->  baixa todas as imagens  ->  enem/<ano>/img/
03_gerar_explicacoes.py ->  chama Gemini uma vez por questao  ->  preenche campo "explicacao"
```

## Por que existe?

Antes, o app fazia 1 requisicao a `api.enem.dev` por questao (90 por prova) e chamava o Gemini sob demanda para explicar respostas. Isso era:

- Lento (API as vezes da timeout, retorna 404 ou imagem quebrada)
- Cara em quota (cada usuario gasta sua chave Gemini ao revisar)
- Frao**gil offline

Agora o dataset e estatico e servido pelo `raw.githubusercontent.com`. So o "Simulado IA" (questoes geradas dinamicamente) continua usando Gemini ao vivo.
