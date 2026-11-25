# Análise Defensiva — Sistema de Distribuição IPTV ("EXTRATOR-V10")

**Documento:** AntiPiracy Defense Lab
**Classificação:** Uso interno / entrega ao cliente
**Natureza:** Engenharia reversa CONCEITUAL + estratégia defensiva
**Dados:** 100% sintéticos. Nenhuma chave DRM real foi extraída, nenhum
token real foi capturado, nenhum conteúdo protegido foi retransmitido.

> Este documento NÃO ensina a quebrar DRM nem a extrair tokens. Ele descreve,
> em nível de arquitetura, os módulos observados nas evidências e propõe as
> CONTRA-MEDIDAS que a equipe de engenharia do provedor deve implementar.

---

## 1. Objetivo

Demonstrar, para operadoras e provedores de streaming, a **engenharia de
detecção e bloqueio** de pirataria digital: onde o atacante atua, quais os
indicadores de fraude (IoF) e onde cada "trava" deve ser colocada.

---

## 2. Arquitetura conceitual observada (a partir das evidências)

O sistema analisado apresenta 6 módulos funcionais. A tabela abaixo separa
**fato observado** (o que a interface mostra) de **hipótese técnica** (o que
precisa ser validado):

| Módulo | Fato observado na interface | Hipótese técnica (a validar) |
|---|---|---|
| Dashboard | Painel central com status de provedores, tokens e servidores | Orquestração de contas/tokens |
| Vault de Tokens | Monitor de "saúde/validade" de credenciais | Batimento cardíaco de credenciais |
| Canais & DRM | Catálogo com KID:KEY e selo "Widevine L3" | Comprometimento de chaves/licenças |
| Minhas VPS | Gerenciamento de servidores + deploy SSH | Infraestrutura de redistribuição |
| Gerador de CFG | Geração de arquivos por provedor/qualidade/idioma | Empacotamento de credenciais |
| Canais YouTube | Lista de lives + compatibilidade XUI/VLC | Retransmissão de lives |

> **Atenção:** a presença de campos na interface NÃO prova a validade das
> chaves, nem o método de obtenção, nem o funcionamento real. Separar fato de
> hipótese é essencial para qualquer processo técnico e jurídico.

---

## 3. Modelo de Ameaças (STRIDE simplificado)

| Módulo | Ameaça | Ator | Impacto |
|---|---|---|---|
| Vault de Tokens | Reutilização/roubo de credenciais | Revendedor/operador | Acesso não autorizado ao catálogo |
| Canais & DRM | Exposição de KID:KEY (Widevine L3) | Operador técnico | Quebra da proteção de conteúdo |
| Minhas VPS / Deploy | Redistribuição em massa | Operador/revenda | Distribuição não autorizada |
| Gerador de CFG | Venda de "pacotes" prontos | Revenda | Escala da pirataria |
| Canais YouTube | Retransmissão de lives | Operador | Violação de direitos de transmissão |
| Saúde dos Tokens | Monitorar credenciais válidas | Operador | Fraude continuada |

---

## 4. Indicadores de Fraude (IoF) — o que a defesa deve procurar

| Regra | Indicador detectável | Severidade |
|---|---|---|
| RULE-01 | Mesmo token em múltiplos IPs em janela curta | CRÍTICO |
| RULE-02 | Conta ativa em cidades/regiões incompatíveis | ALTO |
| RULE-03 | User-agent de ferramenta (ffmpeg/curl/python/wget) | CRÍTICO |
| RULE-04 | Credencial embutida na URL de reprodução | ALTO |
| RULE-05 | Sessões simultâneas acima do limite contratado | ALTO |

Estas regras estão **implementadas e funcionando** no painel do AntiPiracy
Defense Lab (motor de detecção em tempo real).

---

## 5. Mapa de Travas (onde colocar a defesa)

| Módulo do atacante | Contra-medida recomendada |
|---|---|
| Vault de Tokens | Rotação de tokens + revogação por IP + MFA + fingerprint de dispositivo |
| Canais & DRM | Watermarking + fingerprint de sessão + rotação de chaves + monitor de licenças |
| Minhas VPS / Deploy | Bloqueio de ASN de datacenter + TLS + assinatura de sessão + rate-limit |
| Gerador de CFG | Auditoria de geração + marca d'água por cliente + expiração de CFG |
| Canais YouTube | Token por sessão com TTL curto + bind de IP + detecção de repuxo |
| Saúde dos Tokens | Rate-limit em endpoints de validação + honeypot tokens |

---

## 6. Procedimentos de resposta a incidentes (resumo)

1. **Detectar** — motor de regras + anomalias (já implementado).
2. **Correlacionar** — agrupar IoFs por conta/ASN/dispositivo.
3. **Revogar** — token/credencial comprometida.
4. **Preservar** — evidência com timestamp e hash SHA256 (cadeia de custódia).
5. **Mitigar** — aplicar a trava do mapa acima.
6. **Reportar** — relatório técnico com fato vs. hipótese separados.

---

## 7. Conclusão

A plataforma AntiPiracy Defense Lab entrega o que a equipe de engenharia de
uma operadora precisa para **colocar as travas**: indicadores de fraude,
modelo de ameaças e contramedidas — sem cometer qualquer ato de pirataria.

É uma demonstração **prática e vendável** da capacidade defensiva.
