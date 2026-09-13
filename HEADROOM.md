# Headroom no aifood

## Escopo

Headroom e uma dependencia de desenvolvimento (`headroom-ai[proxy]==0.37.0`),
instalada em venv. O codigo upstream nao e copiado nem incorporado como submodulo.
Licenca upstream: Apache-2.0. Nao ha servico pago de compressao contratado.

## Instalar e usar

Requisitos: Python 3.10+, acesso ao PyPI na instalacao e Codex CLI no PATH,
com o login habitual ja configurado. No Linux, use `python3` se necessario.

Na raiz deste repositorio:

```powershell
python headroom_codex.py install
python headroom_codex.py check
python headroom_codex.py run
# Argumentos opcionais para o Codex:
python headroom_codex.py run -- resume
```

O venv padrao e `.venv-headroom`, ignorado pelo Git. Para usar outro venv:

```powershell
python headroom_codex.py --runtime CAMINHO_DO_VENV check
python headroom_codex.py --runtime CAMINHO_DO_VENV run
```

`run` chama o wrapper oficial `headroom wrap codex --code-memory none`.
Ele inicia o proxy e registra o MCP de recuperacao no config do Codex do usuario.
Esse registro e persistente; o roteamento do modelo e aplicado ao processo lancado.
O launcher preserva modelo, esforco, autenticacao e o diretorio de estado do Codex.
O wrapper pode desabilitar entradas legadas Serena/tokensave que o proprio Headroom
tenha instalado; nao execute sobre uma configuracao legada sem revisa-la.

## Aplicativo Codex desktop

Para disponibilizar as ferramentas MCP neste projeto:

```powershell
python headroom_codex.py configure-mcp
```

O comando gera `.codex/config.toml` com caminho absoluto do executavel, somente
se o arquivo estiver ausente ou ja tiver exatamente o conteudo esperado. Arquivos
existentes diferentes exigem revisao; nao sao sobrescritos. A configuracao e local
e ignorada pelo Git. Ao mover o repo ou o runtime, revise o caminho gerado.

Abra esta pasta como projeto confiavel no Codex e inicie uma nova sessao. O MCP
oferece ferramentas de compressao, recuperacao e estatisticas; sua disponibilidade
nao significa que todo o trafego do aplicativo esteja passando pelo proxy.

Para manter um proxy em primeiro plano, quando necessario:

```powershell
python headroom_codex.py proxy
```

A compressao automatica e o caminho `run` do CLI. A ativacao do proxy no transporte
do aplicativo desktop nao e realizada por este repositorio. O Codex ignora ajustes
de provedor/base URL no config de projeto; eles pertencem ao config do usuario.
Nao substitua o provedor ou o modelo para tentar contornar isso.

## Fluxo e dados

1. Codex CLI envia as requisicoes ao proxy local iniciado pelo wrapper.
2. Headroom comprime conteudo elegivel e encaminha ao provedor configurado.
3. Codex recebe a resposta; o MCP permite recuperar originais de marcadores CCR.

Credenciais continuam no mecanismo de autenticacao do Codex. O proxy participa
do transporte autenticado e pode acessar o conteudo e os headers da requisicao;
nao e um cofre de senhas. Nao versionar `auth.json`, chaves, tokens ou `.env`.
Nenhuma credencial e lida ou copiada pelo launcher.

Padroes deste launcher: proxy local; `HEADROOM_BEACON=off`,
`HEADROOM_TELEMETRY=off`, `HEADROOM_STATELESS=true`,
`HEADROOM_CCR_BACKEND=memory`, `HEADROOM_CODE_MEMORY=none`.
`--memory`, `--learn` e Serena nao sao ativados. Segundo Cerebro permanece como
fonte de memoria. O cache CCR e temporario, para desfazer compressao, e desaparece
ao encerrar o processo; marcadores antigos podem deixar de ser recuperaveis.

## Validacao e limites

`check` verifica versao fixada, dependencias e executavel Codex sem chamada ao LLM.
Os testes do launcher podem ser executados com:

```powershell
python -m unittest test_headroom_codex -v
```

A economia depende das entradas, cache do provedor e tarefa. Nao inferir reducao
da cota do plano Codex a partir de percentuais de compressao de testes sinteticos.
Uma sessao real precisa validar transporte, recuperacao CCR e qualidade da resposta.
Nao habilitar dois wrappers concorrentes na mesma porta ou configuracao.

Validacao local em 2026-09-13: Python 3.14, Headroom 0.37.0 e Codex CLI 0.153.4;
`pip check` e tres testes do launcher passaram. Um cliente MCP inicializou as tres
ferramentas, comprimiu 200 registros JSON sinteticos, preservou um marcador `FATAL`
e recuperou o original integralmente. Nao houve chamada real ao modelo. O MCP
funcionou sem proxy ativo; o teste nao comprova roteamento automatico do Codex.

Para voltar ao uso habitual, encerre a sessao encapsulada e execute `codex`
diretamente. O registro MCP pode permanecer no config do usuario; revise somente
o bloco Headroom antes de remove-lo. Nao restaure backups globais indiscriminadamente.

## Referencias

- [Headroom upstream](https://github.com/headroomlabs-ai/headroom)
- [Instalacao](https://docs.headroomlabs.ai/docs/installation)
- [Recuperacao de sessoes Codex](https://docs.headroomlabs.ai/docs/codex-recovery)
- [Configuracao avancada do Codex](https://learn.chatgpt.com/docs/config-file/config-advanced)
- [MCP no Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
