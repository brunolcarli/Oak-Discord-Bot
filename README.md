<table align="center"><tr><td align="center" width="9999">

<img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRejczcPLNHPb4_UAPOEj9jpi3irx7o35Wkk11DQXpOKVI39ENPIg" align="center" width="150" alt="Project icon">

# ABP Oak Discord Bot

[![Wiki badge](https://badgen.net/badge/docs/github_wiki?icon=github)](https://github.com/brunolcarli/Oak-Discord-Bot/wiki)
[![Discord invite](https://badgen.net/badge/icon/discord?icon=discord&label)](![](https://badgen.net/badge/icon/discord?icon=discord&label))
![Generic badge](https://img.shields.io/badge/version-0.0.3-green.svg)

PokeBot auxiliar da Arena de Batalhas Pokémon utilizado no Discord


</td></tr></table>


# Adicionando o Oak ao seu Servidor

Se você não é desenvolvedor e não quer customizar um bot, mas gostaria de utilizar
o `Oak` no seu servidor, basta utilizar este link:

https://discordapp.com/api/oauth2/authorize?client_id=590673073087315968&permissions=18432&scope=bot

Isto é um convite para utilizar o `Oak` no seu servidor Discord, basta colar no seu navegador e dar permissão de acesso ao bot para que ele possa participar dos seus canais Discord no servidor de sua preferência.

Veja a [documentação](https://github.com/brunolcarli/Oak-Discord-Bot/wiki) para conhecer os comandos do bot ou apenas execute no chat do discord:

```
/help
```

https://discordapp.com/api/oauth2/authorize?client_id=590673073087315968&permissions=18432&scope=bot

# Desenvolvedores

Se você é desenvolvedor e gostaria de customizar o `Oak` com seus próprios
comandos siga as instruções abaixo para rodar o bot na sua máquina.

# Instalando e rodando

## Dependências mínimas:

```
Python >=3.4.3 || <=3.6.6
Conta no Discord
```

Crie uma aplicação no Discord, você precisará gerar um `token` para utilizar o seu bot nos servidores Discord.

Poderá seguir [este tutoral](https://medium.com/@moomooptas/how-to-make-a-simple-discord-bot-in-python-40ed991468b4) para fazer isto.

Assim que tiver gerado seu `token` e dado acesso ao bot via página do Discord Developers, crie na raiz deste projeto um arquivo chamado `.env` e nele insira seu token desta forma:


```
TOKEN=dgyausgdhuisegfdyuesnciosbedtyfvdsvufsuydtfcgjksgfdytsd
```

Alguns comandos são direcionados à API [Bill](https://github.com/brunolcarli/Bill) no backend para gravação permanente de dados.
Neste caso é preciso que o server seja levantado e o host seja inserido no mesmo arquivo `.env`.

Ex:

```
BILL=http://localhost:3122/graphql/
```


## Rodando Localmente

Crie um ambiente virtual ([virtualenv](https://docs.python-guide.org/dev/virtualenvs/)) para a instalação das dependências


Instale as dependências executando:

```
make install
```

Assim que as dependências tiverem sido instaladas execute:

```
make init
```

Uma mensagem `The bot is ready!` será exibida informando que o bot está executando.

## Alterando a versão

Sempre que uma nova feature for incluída, utilize o comando:

```
bumpversion patch
```
