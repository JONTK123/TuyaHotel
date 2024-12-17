import React, { useEffect, useState } from "react";
import { Box, CircularProgress, Typography, Alert, Button } from "@mui/material";
import axios from "axios";
import Notification from "./Notification";

const Devices = () => {
    const [devices, setDevices] = useState<any[]>([]); // Lista de dispositivos
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [notifications, setNotifications] = useState<string[]>([]);
    const [processingDevice, setProcessingDevice] = useState<string | null>(null); // Gerencia o estado de processamento de um dispositivo específico
    const [roomNumber, setRoomNumber] = useState("");
    const room_id = "quarto_1";

    useEffect(() => {
        const connectWebSocket = () => {
            const ws = new WebSocket(`ws://localhost:8000/ws/notifications/${room_id}`);
            console.log("conectado ao websocket👌")
            setRoomNumber(room_id);

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log("Dados recebidos do WebSocket:", data);

                    if (!data.type) {
                        throw new Error("Certifique-se de que o Banco de Dados possui quartos..."); // Verifica se o objeto possui a chave "type"
                    }

                    if (data.type === "pulsar_notification") {
                        console.log("Notificação Tuya recebida:", data.data); // Log para notificação
                        const notificationMessage = `Atualização recebida: ${JSON.stringify(data.data)}`;
                        setNotifications((prev) => {
                            const newNotifications = [...prev, notificationMessage];
                            return newNotifications.slice(-10); // Mantém apenas as últimas 10 notificações
                        });
                    } else if (data.type === "device_state") {
                        // Atualiza os estados dos dispositivos recebidos
                        if (data.data) {
                            setDevices(data.data);
                            setLoading(false);

                            // Se algum dispositivo estava sendo processado, desativa o estado de processamento
                            if (processingDevice) {
                                setProcessingDevice(null);
                            }
                        }
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
    }, [processingDevice]);

    const handleTurnOnOff = async (device_id: string, stateKey: string, currentState: string) => {
        try {
            setProcessingDevice(device_id); // Define o dispositivo sendo processado
            const endpoint =
                currentState === "ON"
                    ? `http://localhost:8000/devices/${device_id}/switch_off`
                    : `http://localhost:8000/devices/${device_id}/switch_on`;

            await axios.post(endpoint, {
                properties: { [stateKey]: currentState === "ON" ? false : true },
            });

            console.log("Comando enviado para o backend. Aguardando atualização do estado...");
        } catch (err: any) {
            console.error("Erro ao alternar estado:", err);
            setError(err.response?.data?.detail || "Erro na comunicação com o servidor.");
            setProcessingDevice(null); // Finaliza o estado de processamento em caso de erro
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
                Painel de Dispositivos do quarto {roomNumber}
            </Typography>

            {devices.length > 0 ? (
                devices.map((device, index) => (
                    <Box key={index} sx={{ border: "1px solid #ccc", padding: 2, marginBottom: 2 }}>
                        <Typography variant="h6">{device.name}</Typography>
                        <Typography variant="body2">Categoria: {device.category}</Typography>
                        <Typography variant="body2">Online: {device.isOnline ? "Sim" : "Não"}</Typography>

                        {/* Renderiza os estados do dispositivo */}
                        {Object.keys(device.states).map((key) => (
                            <Typography key={key} variant="body2">
                                {key}: {device.states[key]}
                            </Typography>
                        ))}

                        {/* Botão para ligar/desligar */}
                        {device.states["switch_led"] !== undefined && (
                            <Button
                                variant="contained"
                                color={device.states["switch_led"] === "ON" ? "secondary" : "primary"}
                                onClick={() => handleTurnOnOff(device.id, "switch_led", device.states["switch_led"])}
                                disabled={processingDevice === device.id}
                                style={{ marginTop: "10px" }}
                            >
                                {processingDevice === device.id
                                    ? "Processando..."
                                    : device.states["switch_led"] === "ON"
                                    ? "Desligar"
                                    : "Ligar"}
                            </Button>
                        )}

                        {device.category === "interruptor" &&
                            ["switch_1", "switch_2", "switch_3"].map((key) =>
                                device.states[key] !== undefined ? (
                                    <Button
                                        key={key}
                                        variant="contained"
                                        color={device.states[key] === "ON" ? "secondary" : "primary"}
                                        onClick={() => handleTurnOnOff(device.id, key, device.states[key])}
                                        disabled={processingDevice === device.id}
                                        style={{ marginTop: "10px", marginLeft: "10px" }}
                                    >
                                        {processingDevice === device.id
                                            ? "Processando..."
                                            : device.states[key] === "ON"
                                            ? `${key}: Desligar`
                                            : `${key}: Ligar`}
                                    </Button>
                                ) : null
                            )}
                    </Box>
                ))
            ) : (
                <Typography>Nenhum dispositivo encontrado.</Typography>
            )}

            {/* Notificações */}
            {notifications.map((message, index) => (
                <Notification
                    key={index}
                    message={message}
                    onClose={() => handleRemoveNotification(index)}
                />
            ))}
        </Box>
    );
};

export default Devices;
