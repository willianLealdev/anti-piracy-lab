# ESTADO — AntiPiracy Defense Lab

## Visão geral
- Sistema DEFENSIVO de demonstração (dados 100% sintéticos).
- NÃO extrai DRM real, NÃO captura token real, NÃO retransmite conteúdo protegido.
- Painel = "ferramenta do pirata" (deve abrir ZERADO, sem apontamento).
- Core (DEFENSE-CORE) = "provedor fake" (deve estar CHEIO: provedores + contas + streams).

## Arquitetura
- `core_server.py` → servidor fake (provedor). Porta padrão 8484 (container 8080).
- `app.py` → painel. Porta 5050 local.
- Banco = JSON (`data/core_state.json`, `data/panel_state.json`, `streams/manifest.json`).
- `CORE_URL` no app.py = `os.environ.get("CORE_URL", "")` → vazio por padrão (CONEXÃO ABERTA).

## Servidor-mãe (VPS EasyPanel)
- IP: 173.249.14.170, porta 8080 (servidor_tv_sky).
- 13 provedores + 9 contas demo.
- Repo GitHub: willianLealdev/anti-piracy-lab (branch main) — 13 branches (um por provedor, sem ports).

## Como subir local (WINDOWS)
- Sempre: `$env:PORT='5050'` (evitar conflito com PORT=3000 do Windows).
- Painel zerado: `$env:CORE_URL=''` e rodar `python app.py`.
- Core local (se quiser testar sem VPS): `$env:PORT='8484'; python core_server.py`.

## LIÇÃO IMPORTANTE (não esquecer)
- Ao reiniciar o painel, SEMPRE matar processos órfãos: `Get-NetTCPConnection -LocalPort 5050 -State Listen`
- Já houve processo órfão (PID 51088) servindo dados fake em memória, fazendo parecer que o painel não zerava.

## Contas demo (no core)
- demo.valido / Sky2026@Ok (GloboPlay, OK)
- demo.senha / Sky2026@Ok (GloboPlay, usar senha errada)
- demo.expirado / Sky2026@Ok (GloboPlay, expirada)
- demo.bloqueado / Sky2026@Ok (Sky+, bloqueada)
- demo.telas / Sky2026@Ok (Prime, limite 2/2)
- demo.geo / Sky2026@Ok (GloboPlay, geo anomalia)
- demo.pluto / Pluto2026@Ok (Pluto FAST)
- demo.record / Record2026@Ok (Record FAST)
- demo.youtube / Youtube2026@Ok (YouTube)

## Logins que funcionam hoje (testado)
- Painel local: http://127.0.0.1:5050 (zerado, digitar servidor manualmente)
- Servidor-mãe: http://173.249.14.170:8080
