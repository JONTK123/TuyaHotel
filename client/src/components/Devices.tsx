import React, { useEffect, useState, useRef } from "react";
import {
    Box,
    CircularProgress,
    Typography,
    Alert,
    Button,
    Select,
    MenuItem,
    SelectChangeEvent,
} from "@mui/material";
import axios from "axios";

const Devices = () => {
    const [devices, setDevices] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [notifications, setNotifications] = useState<string[]>([]);
    const [selectedRoom, setSelectedRoom] = useState<string>("quarto_1");
    const [waitingForDeviceUpdate, setWaitingForDeviceUpdate] = useState<boolean>(false);

    const wsRef = useRef<WebSocket | null>(null);
    const isFirstLoad = useRef<boolean>(true);

    useEffect(() => {
        if (isFirstLoad.current) {
            isFirstLoad.current = false;
            return;
        }

        const connectWebSocket = () => {
            if (wsRef.current) {
                console.log("Fechando conexão anterior...");
                wsRef.current.close();
            }

            setDevices([]);
            setError("");
            setLoading(true);

            wsRef.current = new WebSocket(
                `ws://localhost:8000/ws/notifications/${selectedRoom}`
            );
            console.log(`Tentando conectar ao WebSocket do ${selectedRoom}`);

            wsRef.current.onopen = () => {
                console.log("Conexão WebSocket aberta!");
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
                        setWaitingForDeviceUpdate(false); // Libera o botão ao receber o estado atualizado
                    } else if (data.type === "pulsar_notification") {
                        const notificationMessage = `Atualização recebida: ${JSON.stringify(
                            data.data
                        )}`;
                        setNotifications((prev) => [...prev, notificationMessage].slice(-10));
                    }
                } catch (error) {
                    console.error("Erro ao processar os dados do WebSocket:", error);
                    setError("Erro ao processar os dados do WebSocket.");
                }
            };

            wsRef.current.onerror = () => {
                setError("Erro ao conectar ao WebSocket.");
                setLoading(false);
            };

            wsRef.current.onclose = () => {
                console.log(`Conexão encerrada para o ${selectedRoom}.`);
            };
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                console.log("Limpando conexão WebSocket...");
                wsRef.current.close();
            }
        };
    }, [selectedRoom]);

    useEffect(() => {
        setSelectedRoom("quarto_1");
    }, []);

    const handleRoomChange = (event: SelectChangeEvent<string>) => {
        setSelectedRoom(event.target.value as string);
    };

    const handleTurnOnOff = async (
        device_id: string,
        stateKey: string,
        currentState: string
    ) => {
        try {
            setWaitingForDeviceUpdate(true); // Aguarda a atualização via WebSocket

            const endpoint =
                currentState === "ON"
                    ? `http://localhost:8000/api/devices/${device_id}/switch_off`
                    : `http://localhost:8000/api/devices/${device_id}/switch_on`;

            await axios.post(endpoint, {
                properties: { [stateKey]: currentState === "ON" ? false : true },
            });

            console.log("Comando enviado para o backend. Aguardando atualização do estado...");
        } catch (err: any) {
            console.error("Erro ao alternar estado:", err);
            setError(
                err.response?.data?.detail || "Erro na comunicação com o servidor."
            );
            setWaitingForDeviceUpdate(false);
        }
    };

    return (
        <Box sx={{ padding: 2 }}>
            <Typography variant="h5" gutterBottom>
                Dispositivos do {selectedRoom}
            </Typography>

            {/* Seletor de Quartos */}
            <Box sx={{ marginBottom: 2 }}>
                <Select
                    value={selectedRoom}
                    onChange={handleRoomChange}
                    style={{ minWidth: 120 }}
                >
                    <MenuItem value="quarto_1">Quarto 1</MenuItem>
                    <MenuItem value="quarto_2">Quarto 2</MenuItem>
                    <MenuItem value="quarto_3">Quarto 3</MenuItem>
                </Select>
            </Box>

            {/* Carregamento */}
            {loading && (
                <Box
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    height="300px"
                >
                    <CircularProgress />
                </Box>
            )}

            {/* Erro */}
            {error && (
                <Alert severity="error" style={{ margin: "20px" }}>
                    {error}
                </Alert>
            )}

            {/* Lista de Dispositivos */}
            {!loading && !error
                ? devices.map((device, index) => (
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

                          {/* Botão Ligar/Desligar */}
                          {device.states["switch_led"] !== undefined && (
                              <Button
                                  variant="contained"
                                  color={
                                      device.states["switch_led"] === "ON"
                                          ? "secondary"
                                          : "primary"
                                  }
                                  onClick={() =>
                                      handleTurnOnOff(
                                          device.id,
                                          "switch_led",
                                          device.states["switch_led"]
                                      )
                                  }
                                  style={{ marginTop: "10px" }}
                              >
                                  {device.states["switch_led"] === "ON"
                                      ? "Desligar"
                                      : "Ligar"}
                              </Button>
                          )}
                      </Box>
                  ))
                : null}
        </Box>
    );
};

export default Devices;