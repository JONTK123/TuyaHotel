import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    Box,
    CircularProgress,
    Alert,
    Typography,
    Card,
    IconButton,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    TextField,
} from "@mui/material";
import DoNotDisturbIcon from "@mui/icons-material/DoNotDisturb";
import CleaningServicesIcon from "@mui/icons-material/CleaningServices";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsActive";
import axios from "axios";

interface Device {
    id: string;
    name: string;
    category_name: string;
    category: string;
    states: {
        do_not_disturb: string;
        cleaning: string;
        bell: string;
    };
}

interface Room {
    room_id: string;
    devices: Device[];
}

const Rooms: React.FC = () => {
    const [rooms, setRooms] = useState<Room[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();
    const [dialogOpen, setDialogOpen] = useState(false);
    const [newRoomId, setNewRoomId] = useState("");
    const [availableDevices, setAvailableDevices] = useState<Device[]>([]);
    const [selectedDevices, setSelectedDevices] = useState<Device[]>([]);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [roomToDelete, setRoomToDelete] = useState<string | null>(null);
    const [dialogError, setDialogError] = useState<string | null>(null);

    useEffect(() => {
        setRooms([]);
        setError(null);
        setLoading(true);
        const ws = new WebSocket("ws://localhost:8000/ws/central_monitor");

        ws.onopen = () => {
            console.log("Conexão com o WebSocket estabelecida.");
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === "room_switch") {
                    const sortedRooms = data.data.sort((a: Room, b: Room) => {
                        const aCleaning = a.devices.some((d) => d.states.cleaning === "ON") ? 1 : 0;
                        const bCleaning = b.devices.some((d) => d.states.cleaning === "ON") ? 1 : 0;
                        return bCleaning - aCleaning;
                    });

                    setRooms(sortedRooms);
                    setLoading(false);
                } else if (data.type === "error") {
                    setError(data.data);
                    setLoading(false);
                }
            } catch (err) {
                console.error("Erro ao processar dados do WebSocket:", err);
                setError("Erro ao processar os dados recebidos.");
            }
        };

        ws.onerror = () => {
            setError("Erro ao conectar ao WebSocket.");
            setLoading(false);
        };

        ws.onclose = () => {
            console.log("Conexão com o WebSocket encerrada.");
        };

        return () => {
            ws.close();
        };
    }, []);

    const fetchDevices = async () => {
        try {
            const response = await axios.get("http://127.0.0.1:8000/devices");
            const allDevices = response.data.devices || [];

            // Obter dispositivos já utilizados
            const usedDeviceIds = rooms
                .flatMap((room) => room.devices)
                .map((device) => device.id);

            // Filtrar dispositivos disponíveis
            const available = allDevices.filter((device: Device) => !usedDeviceIds.includes(device.id));

            setAvailableDevices(available);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao buscar dispositivos disponíveis.");
        }
    };

    const handleAction = async (device_id: string, currentState: string, stateKey: string) => {
        try {
            const endpoints: { [key: string]: string } = {
                do_not_disturb: currentState === "ON"
                    ? `/api/devices/${device_id}/DoNotDisturbDeactivate`
                    : `/api/devices/${device_id}/DoNotDisturbActivate`,
                cleaning: currentState === "ON"
                    ? `/api/devices/${device_id}/CleaningDeactivate`
                    : `/api/devices/${device_id}/CleaningActivate`,
                bell: currentState === "ON"
                    ? `/api/devices/${device_id}/BellDeactivate`
                    : `/api/devices/${device_id}/BellActivate`,
            };

            const endpoint = `http://localhost:8000${endpoints[stateKey]}`;
            await axios.post(endpoint);

            setRooms((prevRooms) =>
                prevRooms.map((room) =>
                    room.devices.some((device) => device.id === device_id)
                        ? {
                              ...room,
                              devices: room.devices.map((device) =>
                                  device.id === device_id
                                      ? {
                                            ...device,
                                            states: {
                                                ...device.states,
                                                [stateKey]: currentState === "ON" ? "OFF" : "ON",
                                            },
                                        }
                                      : device
                              ),
                          }
                        : room
                )
            );
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro na comunicação com o servidor.");
        }
    };

    const handleAddRoom = async () => {
        if (!newRoomId.trim()) {
            setDialogError("Número do quarto é obrigatório.");
            return;
        }

        const interruptorQuartoCount = selectedDevices.filter((device) => device.name.startsWith("Interruptor Quarto")).length;
        if (interruptorQuartoCount > 1) {
            setDialogError("Você só pode adicionar um dispositivo com o nome 'Interruptor Quarto'.");
            return;
        }

        try {
            const roomData = {
                room_id: newRoomId,
                devices: selectedDevices.map((device) => ({
                    id: device.id,
                    name: device.name,
                    category_name: device.category_name,
                    category: device.category,
                    states: device.states || {},
                })),
            };

            await axios.post("http://127.0.0.1:8000/add_rooms", roomData);
            setDialogOpen(false);
            setNewRoomId("");
            setSelectedDevices([]);
            setDialogError(null);

            window.location.reload();
        } catch (err: any) {
            setDialogError(err.response?.data?.detail || "Erro ao adicionar quarto.");
        }
    };

    const handleDeleteRoom = (roomId: string) => {
        setDeleteConfirmOpen(true);
        setRoomToDelete(roomId);
    };

    const confirmDeleteRoom = async () => {
        if (roomToDelete) {
            try {
                await axios.delete(`http://127.0.0.1:8000/delete_room/${roomToDelete}`);
                window.location.reload();
            } catch (err: any) {
                setError(err.response?.data?.detail || "Erro ao deletar quarto.");
            }
        }
        setDeleteConfirmOpen(false);
        setRoomToDelete(null);
    };

    const cancelDeleteRoom = () => {
        setDeleteConfirmOpen(false);
        setRoomToDelete(null);
    };

    return (
        <Box
            sx={{
                backgroundColor: "#000",
                minHeight: "100vh",
                padding: 2,
                color: "#fff",
                position: "relative",
            }}
        >
            <Typography
                variant="h4"
                gutterBottom
                sx={{ textAlign: "center", color: "#fff" }}
            >
                Monitoramento de Quartos
            </Typography>

            {loading && (
                <Box display="flex" justifyContent="center" marginTop={2}>
                    <CircularProgress sx={{ color: "#fff" }} />
                </Box>
            )}

            {error && (
                <Alert severity="error" sx={{ marginTop: 2 }}>
                    {typeof error === "string" ? error : JSON.stringify(error)}
                </Alert>
            )}

            <Button
                onClick={() => {
                    fetchDevices();
                    setDialogOpen(true);
                }}
                variant="contained"
                sx={{
                    backgroundColor: "#4CAF50",
                    color: "#fff",
                    position: "fixed",
                    bottom: 16,
                    right: 16,
                }}
            >
                Adicionar Quarto
            </Button>

            <Dialog
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
                PaperProps={{
                    sx: {
                        backgroundColor: "#333",
                        color: "#fff",
                    },
                }}
            >
                <DialogTitle>Adicionar Quarto</DialogTitle>
                <DialogContent>
                    <TextField
                        label="Número do Quarto"
                        fullWidth
                        variant="outlined"
                        value={newRoomId}
                        onChange={(e) => setNewRoomId(e.target.value)}
                        sx={{ marginBottom: 2, input: { color: "#fff" }, label: { color: "#fff" } }}
                    />

                    {dialogError && (
                        <Alert severity="error" sx={{ marginBottom: 2 }}>
                            {dialogError}
                        </Alert>
                    )}

                    <Typography variant="body1">Selecionar Dispositivos:</Typography>
                    <Box sx={{ maxHeight: 200, overflowY: "auto" }}>
                        {availableDevices.map((device) => (
                            <Box key={device.id} sx={{ display: "flex", alignItems: "center" }}>
                                <input
                                    type="checkbox"
                                    checked={selectedDevices.some((d) => d.id === device.id)}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setSelectedDevices([...selectedDevices, device]);
                                        } else {
                                            setSelectedDevices(selectedDevices.filter((d) => d.id !== device.id));
                                        }
                                    }}
                                />
                                <Typography sx={{ marginLeft: 1 }}>{device.name}</Typography>
                            </Box>
                        ))}
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)} sx={{ color: "#fff", backgroundColor: "#f44336" }}>
                        Cancelar
                    </Button>
                    <Button onClick={handleAddRoom} sx={{ color: "#fff", backgroundColor: "#4CAF50" }}>
                        Adicionar
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog
                open={deleteConfirmOpen}
                onClose={cancelDeleteRoom}
                PaperProps={{
                    sx: {
                        backgroundColor: "#333",
                        color: "#fff",
                    },
                }}
            >
                <DialogTitle>Confirmar Exclusão</DialogTitle>
                <DialogContent>
                    <Typography>Tem certeza que deseja deletar este quarto?</Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={cancelDeleteRoom} sx={{ color: "#fff", backgroundColor: "#f44336" }}>
                        Cancelar
                    </Button>
                    <Button onClick={confirmDeleteRoom} sx={{ color: "#fff", backgroundColor: "#4CAF50" }}>
                        Confirmar
                    </Button>
                </DialogActions>
            </Dialog>

            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                    gap: 2,
                    marginTop: 2,
                }}
            >
                {rooms.map((room) => {
                    const smartSwitches = room.devices.filter((d) => d.name.startsWith("Interruptor Quarto"));

                    const hasDoNotDisturb = smartSwitches.some((d) => d.states.do_not_disturb === "ON");
                    const hasCleaning = smartSwitches.some((d) => d.states.cleaning === "ON");
                    const isActive = smartSwitches.some((d) => d.states.bell === "ON");

                    return (
                        <Card
                            key={room.room_id}
                            sx={{
                                backgroundColor: "#333",
                                color: "#fff",
                                border: "1px solid #444",
                                borderRadius: "8px",
                                boxShadow: "0 4px 8px rgba(0, 0, 0, 0.5)",
                                ":hover": {
                                    backgroundColor: "#444",
                                    cursor: "pointer",
                                },
                                padding: "16px",
                                textAlign: "center",
                            }}
                            onClick={() => navigate(`/devices/${room.room_id}`)}
                        >
                            <Typography
                                variant="h6"
                                sx={{
                                    backgroundColor: "#4CAF50",
                                    color: "#fff",
                                    textAlign: "center",
                                    borderRadius: "4px",
                                    padding: "4px",
                                    marginBottom: "12px",
                                    fontSize: "16px",
                                }}
                            >
                                Quarto {room.room_id}
                            </Typography>

                            {smartSwitches.map((device) => (
                                <React.Fragment key={device.id}>
                                    <Box sx={{ marginBottom: "16px" }}>
                                        <IconButton
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (!hasCleaning) {
                                                    handleAction(device.id, device.states.do_not_disturb, "do_not_disturb");
                                                }
                                            }}
                                            disabled={hasCleaning}
                                            sx={{
                                                cursor: hasCleaning ? "not-allowed" : "pointer",
                                            }}
                                        >
                                            <DoNotDisturbIcon
                                                sx={{
                                                    fontSize: 50,
                                                    color: device.states.do_not_disturb === "ON" ? "green" : "lightgray",
                                                }}
                                            />
                                        </IconButton>
                                        <Typography variant="body2">Não Perturbe</Typography>
                                    </Box>

                                    <Box sx={{ marginBottom: "16px" }}>
                                        <IconButton
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (!hasDoNotDisturb) {
                                                    handleAction(device.id, device.states.cleaning, "cleaning");
                                                }
                                            }}
                                            disabled={hasDoNotDisturb}
                                            sx={{
                                                cursor: hasDoNotDisturb ? "not-allowed" : "pointer",
                                            }}
                                        >
                                            <CleaningServicesIcon
                                                sx={{
                                                    fontSize: 50,
                                                    color: device.states.cleaning === "ON" ? "green" : "lightgray",
                                                }}
                                            />
                                        </IconButton>
                                        <Typography variant="body2">Limpeza</Typography>
                                    </Box>

                                    <Box sx={{ marginBottom: "16px" }}>
                                        <IconButton
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleAction(device.id, device.states.bell, "bell");
                                            }}
                                            sx={{
                                                cursor: "pointer",
                                            }}
                                        >
                                            <NotificationsActiveIcon
                                                sx={{
                                                    fontSize: 50,
                                                    color: device.states.bell === "ON" ? "green" : "lightgray",
                                                }}
                                            />
                                        </IconButton>
                                        <Typography variant="body2">Campainha</Typography>
                                    </Box>
                                </React.Fragment>
                            ))}

                            <Box>
                                <Button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteRoom(room.room_id);
                                    }}
                                    variant="contained"
                                    sx={{ backgroundColor: "#f44336", color: "#fff", marginTop: "8px" }}
                                >
                                    Deletar Quarto
                                </Button>
                            </Box>
                        </Card>
                    );
                })}
            </Box>
        </Box>
    );
};

export default Rooms;