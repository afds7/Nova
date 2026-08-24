# Checklist Manual de QA

## Preparação

- [ ] Abrir o ambiente de staging em uma janela anônima e confirmar que o frontend usa a URL pública do Railway.
- [ ] Confirmar no navegador que não há erros de CORS, `Configuration` do NextAuth ou chamadas para `localhost`.
- [ ] Confirmar que o backend responde a `GET /api/dashboard/` e que o banco está com as migrations atuais.

## Cadastro e diagnóstico

- [ ] Iniciar o diagnóstico, responder todas as perguntas e confirmar que o avanço só ocorre após uma resposta válida.
- [ ] Chegar à tela de cadastro, preencher nome, e-mail e senha válidos e confirmar que o submit mostra progresso sem cliques duplicados.
- [ ] Confirmar que o diagnóstico é salvo e que o aluno é autenticado ou encaminhado para login sem perder o resultado.
- [ ] Repetir com um e-mail já cadastrado e senha diferente → o diagnóstico deve continuar salvo e a tela deve orientar o login da conta existente, sem fingir que o salvamento falhou.
- [ ] Usar área sugerida automaticamente → a sugestão deve permanecer estável ao mover o mouse e a edição manual deve continuar possível.
- [ ] Editar a área sugerida → o texto manual não deve ser substituído por novos renders.
- [ ] Simular OpenAI sem quota → o diagnóstico deve concluir com o plano determinístico e sem erro 500 visível.
- [ ] Recarregar a página no meio do formulário → o sistema deve manter um estado compreensível ou permitir reiniciar sem dados misturados.

## Login e isolamento

- [ ] Entrar com credenciais válidas → deve abrir o menu do próprio perfil.
- [ ] Tentar senha inválida → deve aparecer mensagem orientadora, sem redirecionamento para `?error=Configuration`.
- [ ] Com o usuário A logado, tentar consultar uma evidência, missão ou dashboard usando o ID do usuário B → deve retornar bloqueio ou dados vazios do próprio perfil.
- [ ] Abrir o menu em outra aba e atualizar → o dashboard deve continuar associado ao mesmo perfil.

## Dashboard

- [ ] Confirmar IEP, IEV, competências, missões e portfólio carregados em uma única visão.
- [ ] Confirmar que o texto de evolução é factual/sugestivo e não classifica o aluno como “bom”, “mau” ou “comum”.
- [ ] Confirmar que uma atualização do IEP aparece como registro contextualizado, não como diagnóstico definitivo.
- [ ] Testar dashboard sem histórico → deve aparecer estado vazio orientado, sem erro.

## Missões e fallback de IA

- [ ] Abrir sugestões → cada item deve informar uma competência-alvo decidida pelas regras.
- [ ] Com OpenAI disponível, confirmar que o texto é personalizado, estruturado e usa convite (“uma missão que pode ajudar”).
- [ ] Com OpenAI fora do ar, em rate limit ou sem chave → devem aparecer missões válidas do catálogo, sem erro visível.
- [ ] Atualizar a tela várias vezes em até 15 minutos → a mesma sugestão não deve gerar chamadas repetidas desnecessárias.
- [ ] Confirmar que nenhum nome ou e-mail aparece no prompt/log da chamada externa.
- [ ] Concluir uma missão → deve haver feedback imediato e link para revisar o rascunho.

## Portfólio e evolução

- [ ] Concluir uma missão e confirmar que surge um rascunho editável com `ativo=False`.
- [ ] Confirmar que a conclusão cria uma nova linha em `HistoricoIEP` e não altera a linha anterior.
- [ ] Editar título, descrição e tipo do rascunho → os campos devem permanecer editáveis.
- [ ] Sair da revisão e voltar pelo link → o rascunho deve continuar disponível.
- [ ] Clicar em “Publicar no portfólio” → exigir confirmação explícita, publicar e redirecionar ao menu.
- [ ] Após publicar, confirmar que o aviso de rascunho desaparece do menu e a evidência aparece como ativa no portfólio.
- [ ] Publicar duas vezes → a segunda tentativa deve ser idempotente, sem duplicar evidência.
- [ ] Arquivar uma evidência → ela deve desaparecer da lista ativa, mas continuar registrada como inativa no banco.
- [ ] Selecionar PDF, PNG, JPG e MP4 válidos → upload direto deve mostrar progresso.
- [ ] Tentar extensão não permitida ou arquivo acima do limite → bloquear antes do upload.
- [ ] Interromper o Django depois da presigned URL e antes do PUT → o PUT direto ao storage deve continuar independente do backend.
- [ ] Confirmar que nenhum arquivo de usuário aparece em `MEDIA_ROOT`, `/tmp` ou no volume do Railway.

## PDF

- [ ] Abrir `/portfolio`, filtrar itens e clicar em “Exportar PDF”.
- [ ] Na impressão, confirmar que controles são ocultados e textos/imagens aparecem no documento.
- [ ] Confirmar que uma imagem sem URL pública é tratada como item sem preview, sem quebrar a exportação.
