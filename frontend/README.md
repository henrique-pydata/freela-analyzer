# Freela Analyzer — Frontend

Dashboard web responsivo para desktop e celular. Não há fallback para dados fictícios.

## Desenvolvimento

```sh
npm install
VITE_API_URL=http://127.0.0.1:8000 npm run dev
```

O frontend consulta apenas a API real. A URL da API também pode ser alterada na tela de configuração e fica salva no navegador.

## Produção

Defina `VITE_API_URL` no build com a URL HTTPS pública do backend. O build usa o preset Node Server do Nitro e pode ser executado com:

```sh
npm run build
npm start
```

O layout é responsivo e a sincronização pode ser iniciada pelo botão **Sincronizar** sem bloquear a navegação.
