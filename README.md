# Agent Framework Preview + AG-UI (on Aspire 13)

This Aspire application uses Microsoft Agent Framework (with Next Gen Foundry) and Ag-UI frontend.

## Features
* Demonstrating Microsoft Foundry (next gen) Agents with Tracing with Microsoft Agent Framework
* Demonstrating AG-UI and how it works with `AzureAIClient` on Microsoft Agent Framework
* Demonstrating Aspire 13 capabilities with Python and Typescript integration

## Prerequisite
1. Install [Aspire CLI](https://learn.microsoft.com/en-us/dotnet/aspire/cli/install)
2. Install [uv](https://docs.astral.sh/uv/)
3. Install [pnpm](https://pnpm.io/installation)
4. Install [az cli](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

## Getting Started
1. `az login`
2. `cd app && uv sync`
3. copy .env-example in `/app` and fill in value
4. `cd frontend && pnpm install`
5. `aspire run` to start the application
6. Go to the frontend app, and open the dev tool to observe the events


