# 📊 Monitor PLC Vetores

Sistema desktop desenvolvido em **Python** para monitoramento de CLPs Siemens via **Ethernet**, utilizando a biblioteca **Snap7**. A aplicação realiza a leitura de vetores armazenados em Data Blocks (DBs), apresenta os dados em tempo real por meio de gráficos interativos e permite a exportação das informações coletadas.

## 🚀 Objetivo

O projeto foi desenvolvido com o objetivo de facilitar a visualização e análise de grandes volumes de dados provenientes de CLPs Siemens, oferecendo uma interface intuitiva para monitoramento de processos industriais.

## ✨ Funcionalidades

- Comunicação com CLPs Siemens via Ethernet utilizando Snap7;
- Configuração de IP, Rack e Slot diretamente pela interface;
- Leitura de Data Blocks (DBs);
- Monitoramento de vetores em tempo real;
- Visualização gráfica dos dados;
- Comparação entre múltiplos gráficos;
- Atualização automática das leituras;
- Tratamento de falhas de comunicação;
- Reconexão automática ao PLC;
- Exportação dos dados para análise posterior;
- Interface gráfica desenvolvida com Tkinter.

## 🛠️ Tecnologias utilizadas

- Python 3
- Snap7
- Tkinter
- Matplotlib
- NumPy

## 📷 Interface

A aplicação possui uma interface simples e intuitiva para facilitar o monitoramento das variáveis do PLC em tempo real.

```text
Interface Principal
├── Configuração de conexão
├── Status do PLC
├── Seleção dos DBs
├── Gráficos em tempo real
└── Exportação dos dados
```

## ⚙️ Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/Monitor-PLC-Vetores.git
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Execute a aplicação

```bash
python main.py
```

## 📡 Configuração

Informe os dados de conexão do PLC:

- Endereço IP
- Rack
- Slot

Após conectar, selecione os Data Blocks desejados e inicie o monitoramento.

## 💡 Possíveis aplicações

- Monitoramento de processos industriais;
- Coleta de dados para análise;
- Validação de sinais;
- Testes de sistemas de automação;
- Supervisão de variáveis em tempo real.

## 📌 Melhorias futuras

- Integração com banco de dados;
- Dashboard web;
- Histórico de leituras;
- Alarmes e notificações;
- Exportação para Excel;
- Geração de relatórios automáticos.

## 👨‍💻 Autor

**Miguel de Freitas Santos**

Tecnólogo em Desenvolvimento de Sistemas e Técnico em Eletroeletrônica e Mecatrônica.

LinkedIn: https://www.linkedin.com/in/miguel-santos-505959257

---
Projeto desenvolvido para estudos e aplicações em automação industrial utilizando Python e comunicação com CLPs Siemens.
