import React, { useEffect, useState } from "react";
import { Box, CircularProgress, Typography, Alert, Button } from "@mui/material";
import axios from "axios";
import Notification from "./Notification";

const Devices = () => {
    const [devices, setDevices] = useState<any>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [roomNumber, setRoomNumber] = useState("");
    const [notifications, setNotifications] = useState<string[]>([]);
    const [ligado, setLigado] = useState<boolean | null>(null); // Inicial como null para diferenciar entre "não carregado"
    const [deviceID, setDeviceID] = useState("");
    const [isProcessing, setIsProcessing] = useState(false); // Estado para gerenciar o botão enquanto processa

    useEffect(() => {
        const connectWebSocket = () => {
            const ws = new WebSocket("ws://localhost:8000/ws/notifications");

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === "pulsar_notification") {
                        const notificationMessage = `Atualização recebida: ${JSON.stringify(data.data)}`;
                        setNotifications((prev) => {
                            if (!prev.includes(notificationMessage)) {
                                return [...prev, notificationMessage];
                            }
                            return prev;
                        });
                    } else if (data.type === "device_state") {
                        const switchState = data.data?.properties?.find((prop: any) => prop.code === "switch_led")?.value;
                        setLigado(switchState); // Atualiza com o valor real retornado (true ou false)
                        setDevices(data.data);
                        setLoading(false);
                        setIsProcessing(false); // Finaliza o estado de processamento
                        console.log("Estado do dispositivo atualizado:", data.data);
                    } else if (data.type === "room_number") {
                        setRoomNumber(data.data);
                    } else if (data.type === "device_id") {
                        setDeviceID(data.data);
                    } else {
                        console.warn("Mensagem desconhecida recebida:", data);
                    }
                } catch (error) {
                    console.error("Erro ao processar os dados do WebSocket:", error);
                    setError("Erro ao processar os dados do WebSocket");
                }
            };

            ws.onerror = () => {
                setError("Erro ao conectar ao WebSocket");
            };

            ws.onclose = () => {
                console.log("Conexão WebSocket encerrada. Tentando reconectar...");
                setTimeout(connectWebSocket, 5000);
            };

            return () => ws.close();
        };

        connectWebSocket();
    }, []);

    const handleTurnOnOff = async () => {
        try {
            setIsProcessing(true); // Inicia o estado de processamento
            const endpoint = ligado
                ? `http://localhost:8000/devices/${deviceID}/switch_off`
                : `http://localhost:8000/devices/${deviceID}/switch_on`;

            await axios.post(endpoint);

            console.log("Comando enviado para o backend. Aguardando atualização do estado...");
        } catch (err: any) {
            if (err.response) {
                console.error("Erro ao alternar estado:", err.response.data.detail);
                setError(err.response.data.detail || "Erro desconhecido");
            } else {
                console.error("Erro na comunicação com o servidor:", err.message);
                setError("Erro na comunicação com o servidor.");
            }
            setIsProcessing(false); // Finaliza o estado de processamento em caso de erro
        }
    };

    const handleRemoveNotification = (index: number) => {
        setNotifications((prev) => prev.filter((_, i) => i !== index));
    };

    if (loading)
        return (
            <Box display="flex" justifyContent="center" alignItems="center" height="300px">
                <CircularProgress />
            </Box>
        );

    if (error)
        return (
            <Alert severity="error" style={{ margin: "20px" }}>
                {error}
            </Alert>
        );

    return (
        <Box sx={{ padding: 2 }}>
            <Typography variant="h5" gutterBottom>
                Quarto {roomNumber}
            </Typography>

            <Button
                variant="contained"
                color={ligado ? "secondary" : "primary"}
                onClick={handleTurnOnOff}
                disabled={isProcessing} // Desabilita o botão enquanto processa
                style={{ marginBottom: "20px" }}
            >
                {isProcessing ? "Processando..." : ligado ? "Desligar Luz" : "Ligar Luz"}
            </Button>

            {/* Exibe as notificações */}
            <Box>
                {notifications.map((message, index) => (
                    <Notification
                        key={index}
                        message={message}
                        onClose={() => handleRemoveNotification(index)}
                        duration={3000} // Notificação some após 3 segundos
                    />
                ))}
            </Box>

            {devices.properties && devices.properties.length > 0 ? (
                <Box>
                    {devices.properties.map((device: any, index: number) => (
                        <Box key={index} sx={{ border: "1px solid #ccc", padding: 2, marginBottom: 2 }}>
                            <Typography variant="body1" gutterBottom>
                                {device.code}
                            </Typography>
                            <pre>{JSON.stringify(device, null, 2)}</pre>
                        </Box>
                    ))}
                </Box>
            ) : (
                <Typography>Nenhum dispositivo encontrado.</Typography>
            )}
        </Box>
    );
};

export default Devices;
