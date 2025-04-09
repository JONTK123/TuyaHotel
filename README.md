# TuyaHotel

**TuyaHotel** is a first version prototype and study project, created as a learning tool to support the development of a larger hotel automation and management system.  
This initial version aims to explore the integration of a smart hotel environment using the **Tuya Cloud API**, with a full-stack architecture designed to simulate room and device control in real-time.

This project helps validate technical decisions, test cloud-based IoT integration, and understand the workflow between frontend, backend, and the Tuya ecosystem.

> **Note:** This is an early-stage, experimental version, not intended for production.

---

## Technologies Used (Tech Stack)

- **Backend**: Python (FastAPI)  
- **Frontend**: React  
- **APIs**: Tuya Cloud APIs  
- **Authentication**: Tuya OAuth 2.0 (token-based)  
- **Data Format**: JSON for API communication  
- **Execution Environment**: Localhost (development setup)  

---

## Main Features

### Integration with Tuya Cloud API:
- Authentication using Tuya OAuth 2.0 (client credentials)
- Token lifecycle management (access/refresh)
- Requests for retrieving, listing, and managing IoT devices

### Room & Device Simulation:
- Hotel room registration (mock or static data)
- Device association per room
- Basic state control (on/off, etc.)

### Frontend Interface:
- Built with React for modular and responsive UI
- Communication with FastAPI backend via HTTP
- Visual interface for listing rooms and controlling devices

---

## Purpose of This Version

- Serve as a technical exploration of Tuya's APIs  
- Prototype a full-stack architecture suitable for smart hotel control  
- Build a foundation to scale into a more complex and professional solution  

---

# Visão Geral (Português)

**TuyaHotel** é um protótipo em primeira versão e projeto de estudo, criado como ferramenta de aprendizado para dar suporte ao desenvolvimento de um sistema maior de automação e gerenciamento hoteleiro.  
Esta versão tem como foco explorar a integração de um ambiente hoteleiro inteligente utilizando a **Tuya Cloud API**, com uma arquitetura full-stack que simula o controle de quartos e dispositivos em tempo real.

O projeto ajuda a validar decisões técnicas, testar a integração com infraestrutura IoT baseada em nuvem, e entender o fluxo entre frontend, backend e o ecossistema da Tuya.

> **Nota:** Esta é uma versão experimental e inicial, sem fins de uso em produção.

---

## Tecnologias Utilizadas

- **Backend**: Python (FastAPI)  
- **Frontend**: React  
- **APIs**: Tuya Cloud APIs  
- **Autenticação**: OAuth 2.0 da Tuya (baseada em token)  
- **Formato de Dados**: JSON (para comunicação via API)  
- **Ambiente de Execução**: Localhost (modo de desenvolvimento)  

---

## Funcionalidades Principais

### Integração com a API da Tuya:
- Autenticação com credenciais (Client ID/Secret)
- Gerenciamento de tokens (acesso/renovação)
- Requisições para listar e controlar dispositivos IoT

### Simulação de Quartos e Dispositivos:
- Cadastro de quartos (mock ou dados fixos)
- Associação de dispositivos por quarto
- Controle básico de estado (ligar/desligar etc.)

### Interface Web:
- Desenvolvida com React
- Comunicação via HTTP com backend FastAPI
- Interface para listagem de quartos e controle de dispositivos

---

## Objetivos Desta Versão

- Explorar tecnicamente as APIs da Tuya  
- Prototipar uma arquitetura full-stack para controle hoteleiro inteligente  
- Criar uma base para expansão futura com funcionalidades mais robustas  

Funcionalidades como banco de dados, autenticação de usuários e deploy em produção foram deixadas de fora intencionalmente, para focar no objetivo principal: **criar uma conexão ponta-a-ponta entre interface web e dispositivos inteligentes via Tuya Cloud**.
