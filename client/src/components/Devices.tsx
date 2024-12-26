import React, { useEffect, useState, useRef } from "react";
import {
    Box,
    CircularProgress,
    Typography,
    Alert,
    Button,
} from "@mui/material";
import { useParams } from "react-router-dom";
import axios from "axios";
import Notification from "./Notification"; // Certifique-se de que o caminho esteja correto

const Devices = () => {
    const { roomId } = useParams(); // Captura o roomId da URL
    const [devices, setDevices] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [notifications, setNotifications] = useState<string[]>([]);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const connectWebSocket = () => {
            if (wsRef.current) {
                wsRef.current.close();
            }

            setDevices([]);
            setError("");
            setLoading(true);

            wsRef.current = new WebSocket(
                `ws://localhost:8000/ws/device_panel/${roomId}`
            );

            wsRef.current.onopen = () => {
                setLoading(false);
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === "error") {
                        setError(data.data);
                        setDevices([]);
                    } else if (data.type === "device_state" && data.data) {
                        setDevices(data.data);
                    } else if (data.type === "pulsar_notification") {
                        setNotifications((prev) => [
                            ...prev,
                            `Atualização recebida: ${JSON.stringify(data.data)}`,
                        ].slice(-10));
                    }
                } catch (error) {
                    setError("Erro ao processar os dados do WebSocket.");
                }
            };

            wsRef.current.onerror = () => {
                setError("Erro ao conectar ao WebSocket.");
                setLoading(false);
            };

            wsRef.current.onclose = () => {
                console.log(`Conexão encerrada para o quarto ${roomId}.`);
            };
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [roomId]); // Atualiza o WebSocket quando o roomId muda

    const handleAction = async (
        device_id: string,
        stateKey: string,
        currentState: string,
        action: string
    ) => {
        try {
            const endpoints: { [key: string]: string } = {
                switch: currentState === "ON"
                    ? `/api/devices/${device_id}/switch_off`
                    : `/api/devices/${device_id}/switch_on`,
                doNotDisturb: currentState === "ON"
                    ? `/api/devices/${device_id}/DoNotDisturbDeactivate`
                    : `/api/devices/${device_id}/DoNotDisturbActivate`,
                cleaning: currentState === "ON"
                    ? `/api/devices/${device_id}/CleaningDeactivate`
                    : `/api/devices/${device_id}/CleaningActivate`,
                freeze: `/api/devices/${device_id}/freeze`,
                unfreeze: `/api/devices/${device_id}/unfreeze`,
                turnOff: `/api/devices/${device_id}/turn-off`,
            };

            const endpoint = `http://localhost:8000${endpoints[action]}`;
            await axios.post(endpoint, {
                properties: { [stateKey]: currentState === "ON" ? false : true },
            });
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro na comunicação com o servidor.");
        }
    };

    const removeNotification = (index: number) => {
        setNotifications((prev) => prev.filter((_, i) => i !== index));
    };

    return (
        <Box sx={{ padding: 2 }}>
            <Typography variant="h5" gutterBottom>
                Dispositivos do Quarto {roomId}
            </Typography>

            {notifications.map((notification, index) => (
                <Notification
                    key={index}
                    message={notification}
                    onClose={() => removeNotification(index)}
                />
            ))}

            {loading && (
                <Box display="flex" justifyContent="center" alignItems="center" height="300px">
                    <CircularProgress />
                </Box>
            )}

            {error && (
                <Alert severity="error" style={{ margin: "20px" }}>
                    {error}
                </Alert>
            )}

            {!loading && !error && devices.map((device, index) => (
                <Box
                    key={index}
                    sx={{ border: "1px solid #ccc", padding: 2, marginBottom: 2 }}
                >
                    <Typography variant="h6">{device.name}</Typography>
                    <Typography>Categoria: {device.category}</Typography>
                    <Typography>Online: {device.Online ? "Sim" : "Não"}</Typography>

                    {Object.keys(device.states).map((key) => (
                        <Typography key={key}>
                            {key}: {device.states[key]}
                        </Typography>
                    ))}

                    <Box sx={{ display: "flex", gap: 2, marginTop: "10px" }}>
                        {device.states["switch_led"] !== undefined && (
                            <Button
                                variant="contained"
                                color={
                                    device.states["switch_led"] === "ON"
                                        ? "secondary"
                                        : "primary"
                                }
                                onClick={() =>
                                    handleAction(
                                        device.id,
                                        "switch_led",
                                        device.states["switch_led"],
                                        "switch"
                                    )
                                }
                            >
                                {device.states["switch_led"] === "ON"
                                    ? "Desligar"
                                    : "Ligar"}
                            </Button>
                        )}

                        {device.states["do_not_disturb"] !== undefined && (
                            <Button
                                variant="contained"
                                color={
                                    device.states["do_not_disturb"] === "ON"
                                        ? "secondary"
                                        : "primary"
                                }
                                disabled={device.states["cleaning"] === "ON"} // Desativa botão se Limpeza está ativada
                                onClick={() =>
                                    handleAction(
                                        device.id,
                                        "do_not_disturb",
                                        device.states["do_not_disturb"],
                                        "doNotDisturb"
                                    )
                                }
                            >
                                {device.states["do_not_disturb"] === "ON"
                                    ? "Desativar Não Perturbe"
                                    : "Ativar Não Perturbe"}
                            </Button>
                        )}

                        {device.states["cleaning"] !== undefined && (
                            <Button
                                variant="contained"
                                color={
                                    device.states["cleaning"] === "ON"
                                        ? "secondary"
                                        : "primary"
                                }
                                disabled={device.states["do_not_disturb"] === "ON"} // Desativa botão se Não Perturbe está ativado
                                onClick={() =>
                                    handleAction(
                                        device.id,
                                        "cleaning",
                                        device.states["cleaning"],
                                        "cleaning"
                                    )
                                }
                            >
                                {device.states["cleaning"] === "ON"
                                    ? "Desativar Limpeza"
                                    : "Ativar Limpeza"}
                            </Button>
                        )}

                    </Box>
                </Box>
            ))}
        </Box>
    );
};

export default Devices;