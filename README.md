# TuyaHotel

**TuyaHotel** is a first version prototype and study project, created as a learning tool to support the development of a larger hotel automation and management system.  
This initial version aims to explore the integration of a smart hotel environment using the **Tuya Cloud API**, with a full-stack architecture designed to simulate room and device control in real-time.

This project helps validate technical decisions, test cloud-based IoT integration, and understand the workflow between frontend, backend, and the Tuya ecosystem.

> **Note:** This is an early-stage, experimental version, not intended for production.

---

## Table of Contents

- [Technologies Used](#technologies-used-tech-stack)
- [Main Features](#main-features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Português](#visão-geral-português)

---

## Technologies Used (Tech Stack)

- **Backend**: Python (FastAPI)  
- **Frontend**: React with TypeScript
- **Database**: MongoDB (Motor AsyncIO)
- **APIs**: Tuya Cloud APIs  
- **Authentication**: Tuya OAuth 2.0 (token-based)  
- **Real-time Communication**: WebSocket (native WebSocket API)
- **UI Framework**: Material-UI (MUI)
- **HTTP Client**: Axios
- **Data Format**: JSON for API communication  
- **Execution Environment**: Localhost (development setup)  

---

## Main Features

### Integration with Tuya Cloud API:
- Authentication using Tuya OAuth 2.0 (client credentials)
- Token lifecycle management (access/refresh)
- Requests for retrieving, listing, and managing IoT devices
- Real-time device status updates via WebSocket

### Room & Device Simulation:
- Hotel room registration and management
- Device association per room
- Basic state control (on/off, dimming, etc.)
- Device activity logging

### Frontend Interface:
- Built with React and TypeScript for modular and responsive UI
- Material-UI components for modern design
- Real-time device updates via WebSocket
- Communication with FastAPI backend via HTTP
- Visual interface for listing rooms and controlling devices

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v16 or higher) and npm
- **Python** (v3.8 or higher)
- **MongoDB** (local or cloud instance)
- **Tuya Developer Account** with API credentials
  - Access ID
  - Access Key
  - API Endpoint
  - MQ Endpoint (for real-time updates)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/JONTK123/TuyaHotel.git
cd TuyaHotel
```

### 2. Install Backend Dependencies

```bash
# Install Python dependencies
pip install fastapi uvicorn motor python-dotenv tuya-connector-python
```

**Note:** Consider creating a `requirements.txt` file for better dependency management.

### 3. Install Frontend Dependencies

```bash
# Navigate to client directory
cd client

# Install npm packages
npm install

# Return to root directory
cd ..
```

---

## Configuration

### 1. Create Environment File

Create a `.env` file in the root directory with the following variables:

```env
# Tuya API Credentials
ACCESS_ID=your_tuya_access_id
ACCESS_KEY=your_tuya_access_key
API_ENDPOINT=https://openapi.tuyaus.com
MQ_ENDPOINT=wss://mqe.tuyaus.com:8285/

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=tuya_hotel
COLLECTION_ROOMS=rooms
COLLECTION_DEVICE_LOGS=device_logs
```

### 2. Obtain Tuya API Credentials

1. Create an account at [Tuya IoT Platform](https://iot.tuya.com/)
2. Create a new Cloud Project
3. Subscribe to required APIs (Device Management, Device Control)
4. Copy your Access ID and Access Key
5. Link your Tuya devices to the project

### 3. Configure MongoDB

Ensure MongoDB is running locally or update the `MONGO_URI` in your `.env` file with your MongoDB connection string.

---

## Usage

### Running the Application

#### 1. Start the Backend Server

```bash
# From the root directory
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

#### 2. Start the Frontend Application

```bash
# In a new terminal, navigate to client directory
cd client

# Start the React development server
npm start
```

The frontend will be available at `http://localhost:3000`

### Testing with Mock API

The project includes a mock Tuya API for testing without actual devices. In `server/main.py`, you'll find two lines near the top of the file:

```python
# openapi = initialize_tuya_openapi()
openapi = MockTuyaAPI()
```

- To use the mock API (default), keep it as shown above
- To use the real Tuya API, swap the comments (uncomment the first line and comment the second)

---

## Project Structure

```
TuyaHotel/
├── client/                 # React frontend application
│   ├── public/            # Static files
│   ├── src/               # Source code
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── App.tsx        # Main app component
│   │   └── index.tsx      # Entry point
│   ├── package.json       # Frontend dependencies
│   └── tsconfig.json      # TypeScript configuration
├── server/                # Python backend application
│   ├── main.py            # FastAPI main application
│   ├── tuya_setup.py      # Tuya API initialization
│   ├── database.py        # MongoDB connection
│   ├── models.py          # Data models
│   ├── device_control.py  # Device control routes
│   └── websocket_manager.py # WebSocket management
├── tests/                 # Test files
│   └── MockTuyaAPI.py     # Mock Tuya API for testing
├── .env                   # Environment variables (create this)
├── .gitignore            # Git ignore rules
├── package.json          # Root package configuration
└── README.md             # This file
```

---

## API Documentation

### Backend Endpoints

#### Room Management
- `GET /api/rooms` - List all hotel rooms
- `POST /api/rooms` - Create a new room
- `GET /api/rooms/{room_id}` - Get room details
- `PUT /api/rooms/{room_id}` - Update room information
- `DELETE /api/rooms/{room_id}` - Delete a room

#### Device Control
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device status
- `POST /api/devices/{device_id}/control` - Control device state
- `GET /api/rooms/{room_id}/devices` - List devices in a room

#### WebSocket
- `WS /ws` - WebSocket connection for real-time updates

### Frontend API Calls

The frontend uses Axios to communicate with the backend. All API calls are made to `http://localhost:8000/api`.

---

## Troubleshooting

### Common Issues

**Backend won't start:**
- Ensure all Python dependencies are installed
- Check that MongoDB is running and accessible
- Verify `.env` file exists with correct credentials

**Frontend won't start:**
- Delete `node_modules` and `package-lock.json`, then run `npm install` again
- Clear npm cache: `npm cache clean --force`
- Ensure Node.js version is 16 or higher

**Devices not responding:**
- Verify Tuya API credentials are correct
- Check that devices are linked to your Tuya project
- Ensure devices are online in the Tuya app
- Check API endpoint matches your region (US, EU, CN, IN)

**CORS errors:**
- Ensure the frontend port is listed in the CORS origins in `server/main.py`
- Clear browser cache and restart both servers

**WebSocket connection fails:**
- Check that both servers are running
- Verify firewall settings allow WebSocket connections
- Check browser console for error messages

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Purpose of This Version

- Serve as a technical exploration of Tuya's APIs  
- Prototype a full-stack architecture suitable for smart hotel control  
- Build a foundation to scale into a more complex and professional solution  

---

---

# Visão Geral (Português)

**TuyaHotel** é um protótipo em primeira versão e projeto de estudo, criado como ferramenta de aprendizado para dar suporte ao desenvolvimento de um sistema maior de automação e gerenciamento hoteleiro.  
Esta versão tem como foco explorar a integração de um ambiente hoteleiro inteligente utilizando a **Tuya Cloud API**, com uma arquitetura full-stack que simula o controle de quartos e dispositivos em tempo real.

O projeto ajuda a validar decisões técnicas, testar a integração com infraestrutura IoT baseada em nuvem, e entender o fluxo entre frontend, backend e o ecossistema da Tuya.

> **Nota:** Esta é uma versão experimental e inicial, sem fins de uso em produção.

---

## Índice

- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Como Usar](#como-usar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Documentação da API](#documentação-da-api)
- [Solução de Problemas](#solução-de-problemas)
- [Como Contribuir](#como-contribuir)
- [Licença](#licença)

---

## Tecnologias Utilizadas

- **Backend**: Python (FastAPI)  
- **Frontend**: React com TypeScript
- **Banco de Dados**: MongoDB (Motor AsyncIO)
- **APIs**: Tuya Cloud APIs  
- **Autenticação**: OAuth 2.0 da Tuya (baseada em token)  
- **Comunicação em Tempo Real**: WebSocket (API WebSocket nativa)
- **Framework UI**: Material-UI (MUI)
- **Cliente HTTP**: Axios
- **Formato de Dados**: JSON (para comunicação via API)  
- **Ambiente de Execução**: Localhost (modo de desenvolvimento)  

---

## Funcionalidades Principais

### Integração com a API da Tuya:
- Autenticação usando OAuth 2.0 da Tuya (credenciais de cliente)
- Gerenciamento do ciclo de vida de tokens (acesso/renovação)
- Requisições para recuperar, listar e gerenciar dispositivos IoT
- Atualizações de status de dispositivos em tempo real via WebSocket

### Simulação de Quartos e Dispositivos:
- Registro e gerenciamento de quartos de hotel
- Associação de dispositivos por quarto
- Controle básico de estado (ligar/desligar, dimerização, etc.)
- Registro de atividades dos dispositivos

### Interface Frontend:
- Construída com React e TypeScript para UI modular e responsiva
- Componentes Material-UI para design moderno
- Atualizações de dispositivos em tempo real via WebSocket
- Comunicação com backend FastAPI via HTTP
- Interface visual para listagem de quartos e controle de dispositivos

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Node.js** (v16 ou superior) e npm
- **Python** (v3.8 ou superior)
- **MongoDB** (instância local ou na nuvem)
- **Conta de Desenvolvedor Tuya** com credenciais de API
  - Access ID
  - Access Key
  - API Endpoint
  - MQ Endpoint (para atualizações em tempo real)

---

## Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/JONTK123/TuyaHotel.git
cd TuyaHotel
```

### 2. Instalar Dependências do Backend

```bash
# Instalar dependências Python
pip install fastapi uvicorn motor python-dotenv tuya-connector-python
```

**Nota:** Considere criar um arquivo `requirements.txt` para melhor gerenciamento de dependências.

### 3. Instalar Dependências do Frontend

```bash
# Navegar para o diretório do cliente
cd client

# Instalar pacotes npm
npm install

# Retornar ao diretório raiz
cd ..
```

---

## Configuração

### 1. Criar Arquivo de Ambiente

Crie um arquivo `.env` no diretório raiz com as seguintes variáveis:

```env
# Credenciais da API Tuya
ACCESS_ID=seu_access_id_tuya
ACCESS_KEY=sua_access_key_tuya
API_ENDPOINT=https://openapi.tuyaus.com
MQ_ENDPOINT=wss://mqe.tuyaus.com:8285/

# Configuração do MongoDB
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=tuya_hotel
COLLECTION_ROOMS=rooms
COLLECTION_DEVICE_LOGS=device_logs
```

### 2. Obter Credenciais da API Tuya

1. Crie uma conta na [Plataforma IoT Tuya](https://iot.tuya.com/)
2. Crie um novo Projeto Cloud
3. Inscreva-se nas APIs necessárias (Gerenciamento de Dispositivos, Controle de Dispositivos)
4. Copie seu Access ID e Access Key
5. Vincule seus dispositivos Tuya ao projeto

### 3. Configurar MongoDB

Certifique-se de que o MongoDB está em execução localmente ou atualize o `MONGO_URI` no arquivo `.env` com sua string de conexão MongoDB.

---

## Como Usar

### Executando a Aplicação

#### 1. Iniciar o Servidor Backend

```bash
# Do diretório raiz
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

O backend estará disponível em `http://localhost:8000`

#### 2. Iniciar a Aplicação Frontend

```bash
# Em um novo terminal, navegue até o diretório client
cd client

# Iniciar o servidor de desenvolvimento React
npm start
```

O frontend estará disponível em `http://localhost:3000`

### Testando com API Mock

O projeto inclui uma API Tuya mock para testes sem dispositivos reais. No arquivo `server/main.py`, você encontrará duas linhas no início do arquivo:

```python
# openapi = initialize_tuya_openapi()
openapi = MockTuyaAPI()
```

- Para usar a API mock (padrão), mantenha como mostrado acima
- Para usar a API Tuya real, troque os comentários (descomente a primeira linha e comente a segunda)

---

## Estrutura do Projeto

```
TuyaHotel/
├── client/                 # Aplicação frontend React
│   ├── public/            # Arquivos estáticos
│   ├── src/               # Código fonte
│   │   ├── components/    # Componentes React
│   │   ├── pages/         # Componentes de páginas
│   │   ├── App.tsx        # Componente principal da app
│   │   └── index.tsx      # Ponto de entrada
│   ├── package.json       # Dependências do frontend
│   └── tsconfig.json      # Configuração TypeScript
├── server/                # Aplicação backend Python
│   ├── main.py            # Aplicação principal FastAPI
│   ├── tuya_setup.py      # Inicialização da API Tuya
│   ├── database.py        # Conexão MongoDB
│   ├── models.py          # Modelos de dados
│   ├── device_control.py  # Rotas de controle de dispositivos
│   └── websocket_manager.py # Gerenciamento WebSocket
├── tests/                 # Arquivos de teste
│   └── MockTuyaAPI.py     # API Tuya mock para testes
├── .env                   # Variáveis de ambiente (criar este arquivo)
├── .gitignore            # Regras do Git ignore
├── package.json          # Configuração do pacote raiz
└── README.md             # Este arquivo
```

---

## Documentação da API

### Endpoints do Backend

#### Gerenciamento de Quartos
- `GET /api/rooms` - Listar todos os quartos do hotel
- `POST /api/rooms` - Criar um novo quarto
- `GET /api/rooms/{room_id}` - Obter detalhes do quarto
- `PUT /api/rooms/{room_id}` - Atualizar informações do quarto
- `DELETE /api/rooms/{room_id}` - Deletar um quarto

#### Controle de Dispositivos
- `GET /api/devices` - Listar todos os dispositivos
- `GET /api/devices/{device_id}` - Obter status do dispositivo
- `POST /api/devices/{device_id}/control` - Controlar estado do dispositivo
- `GET /api/rooms/{room_id}/devices` - Listar dispositivos em um quarto

#### WebSocket
- `WS /ws` - Conexão WebSocket para atualizações em tempo real

### Chamadas de API do Frontend

O frontend usa Axios para se comunicar com o backend. Todas as chamadas de API são feitas para `http://localhost:8000/api`.

---

## Solução de Problemas

### Problemas Comuns

**Backend não inicia:**
- Certifique-se de que todas as dependências Python estão instaladas
- Verifique se o MongoDB está em execução e acessível
- Verifique se o arquivo `.env` existe com as credenciais corretas

**Frontend não inicia:**
- Delete `node_modules` e `package-lock.json`, depois execute `npm install` novamente
- Limpe o cache do npm: `npm cache clean --force`
- Certifique-se de que a versão do Node.js é 16 ou superior

**Dispositivos não respondem:**
- Verifique se as credenciais da API Tuya estão corretas
- Verifique se os dispositivos estão vinculados ao seu projeto Tuya
- Certifique-se de que os dispositivos estão online no app Tuya
- Verifique se o endpoint da API corresponde à sua região (US, EU, CN, IN)

**Erros de CORS:**
- Certifique-se de que a porta do frontend está listada nas origens CORS em `server/main.py`
- Limpe o cache do navegador e reinicie ambos os servidores

**Conexão WebSocket falha:**
- Verifique se ambos os servidores estão em execução
- Verifique as configurações do firewall para permitir conexões WebSocket
- Verifique o console do navegador para mensagens de erro

---

## Como Contribuir

Contribuições são bem-vindas! Por favor, siga estes passos:

1. Faça um fork do repositório
2. Crie uma branch de feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

---

## Objetivos Desta Versão

- Explorar tecnicamente as APIs da Tuya  
- Prototipar uma arquitetura full-stack para controle hoteleiro inteligente  
- Criar uma base para expansão futura com funcionalidades mais robustas  

Funcionalidades como banco de dados, autenticação de usuários e deploy em produção foram deixadas de fora intencionalmente, para focar no objetivo principal: **criar uma conexão ponta-a-ponta entre interface web e dispositivos inteligentes via Tuya Cloud**.
