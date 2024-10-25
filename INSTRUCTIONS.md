## Instrucciones para correr el codigo

## Crear el ambiente virtual
```python3 -m venv venv```
## Iniciar el ambiente virtual
```source venv/bin/activate```
## Instalar dependencias 
```pip install -r requirements.txt```
## Correr el codigo 
```python3 agent.py dev```

Poner las api Keys de deepgram, livekit y openai en .env.local
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY`

Se debe exportar la key de openai con este comando
```export OPENAI_API_KEY="your_api_key_here"```

Este agente se conecta con un frontend sandbox que se puede encontrar en estos repositorios: 
- https://github.com/livekit-examples/
- https://github.com/Arteaga0415/sandbox-frontend
