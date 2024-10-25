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
En .env.example estan todas las variables que se deben llenar 
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `LIVEKIT_SIP_URI`


Se debe exportar la key de openai con este comando
```export OPENAI_API_KEY="your_api_key_here"```

Este agente se conecta con un frontend sandbox que se puede encontrar en estos repositorios: 
- https://github.com/livekit-examples/
- https://github.com/Arteaga0415/sandbox-frontend

Para la integracion con twilio (https://docs.livekit.io/sip/quickstart/#preparing-sip-server)
1. Utilizar el numero de telefono obtenido de Twilio (Agregarlo a .env.local)

2. Crear SIP trunk de Twilio: (https://www.twilio.com/docs/sip-trunking#create-a-trunk)

3. Configurar Termination URI, "sfco" sub-domain: (https://www.twilio.com/docs/sip-trunking#termination-uri)
3.1 configurar el Trunk para que apunte a "sfco.pstn.twilio.com"
4. Configurar Autenticacion creando un nuevo "Credential List" con un username y password: (https://www.twilio.com/docs/sip-trunking#authentication)

5. Configurar el rango de IP en Twilio de "0.0.0.0/1" a "128.0.0.0/1"

6. Configurar LiveKit CLI corriendo los siguientes export en la terminal
```
export LIVEKIT_URL=wss://ai-agent-bzr101k5.livekit.cloud
export LIVEKIT_API_KEY=<your API Key>
export LIVEKIT_API_SECRET=<your API Secret>
```
7. Agregar outbound trunk usando las credenciales en el paso 4, correr en la terminal el comando (ya se debe tener el archivo "outboundTrunk.json" con las credenciales y el address con el Trunk): 
```lk sip outbound create outboundTrunk.json```
7.1 Este comando arriba va a imprimir el trunk-id: `SIPTrunkID: <your-trunk-id>` Este se debe poner en el sipParticipant.json

8. Para test una llamada con el archivo `sipParticipant.json` correr ```lk sip participant create sipParticipant.json```

9. Solo si se quiere configurar para recibir llamadas en un futuro correr `create_inbound_trunk.py` para obtener "origination and termination URLs" automaticamente y Seguir los siguientes pasos (https://docs.livekit.io/sip/quickstart/#incoming-calls)