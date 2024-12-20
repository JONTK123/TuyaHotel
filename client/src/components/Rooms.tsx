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
    TextField
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
        bell: string; // Campainha
    };
}

interface Room {
    room_id: string;
    devices: Device[];
}

const Rooms: React.FC = () => {
    const [rooms, setRooms] = useState<Room[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const navigate = useNavigate();
    const [dialogOpen, setDialogOpen] = useState(false);
    const [newRoomId, setNewRoomId] = useState("");
    const [availableDevices, setAvailableDevices] = useState<Device[]>([]);
    const [selectedDevices, setSelectedDevices] = useState<Device[]>([]);

    // Estados para confirmação ao deletar quarto
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [roomToDelete, setRoomToDelete] = useState<string | null>(null);

    useEffect(() => {
        setRooms([]);
        setError("");
        setLoading(true);
        const ws = new WebSocket("ws://localhost:8000/ws/central_monitor");

        ws.onopen = () => {
            console.log("Conexão com o WebSocket estabelecida.");
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "room_switch") {
                    console.log("Dados recebidos:", data.data);
                    setLoading(false);

                    const sortedRooms = data.data.sort((a: Room, b: Room) => {
                        const aCleaning = a.devices.some((d: Device) => d.states.cleaning === "ON") ? 1 : 0;
                        const bCleaning = b.devices.some((d: Device) => d.states.cleaning === "ON") ? 1 : 0;
                        return bCleaning - aCleaning;
                    });

                    setRooms(sortedRooms);
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
            setAvailableDevices(response.data.devices || []);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao buscar dispositivos disponíveis.");
        }
    };

    const handleAction = async (
        device_id: string,
        stateKey: string,
        currentState: string
    ) => {
        try {
            const endpoints: { [key: string]: string } = {
                doNotDisturb: currentState === "ON"
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
            await axios.post(endpoint, {
                properties: { [stateKey]: currentState === "ON" ? false : true },
            });

            console.log(
                `Estado de ${stateKey} do dispositivo ${device_id} foi alterado.`
            );
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro na comunicação com o servidor.");
        }
    };

    const handleAddRoom = async () => {
        try {
            const roomData = {
                room_id: newRoomId,
                devices: selectedDevices.map(device => ({
                    id: device.id,
                    name: device.name,
                    category_name: device.category_name,
                    category: device.category,
                    states: device.states
                }))
            };

            await axios.post("http://127.0.0.1:8000/add_rooms", roomData);
            setDialogOpen(false);
            setNewRoomId("");
            setSelectedDevices([]);

            // Recarrega a página após adicionar um quarto
            window.location.reload();
        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao adicionar quarto.");
        }
    };

    const handleDeleteRoom = async (roomId: string) => {
        setDeleteConfirmOpen(true);
        setRoomToDelete(roomId);
    };

    const confirmDeleteRoom = async () => {
        if (roomToDelete) {
            try {
                await axios.delete(`http://127.0.0.1:8000/delete_room/${roomToDelete}`);
                console.log(`Quarto ${roomToDelete} deletado com sucesso.`);

                // Recarrega a página após deletar um quarto
                window.location.reload();
            }
            catch (err: any) {
                setError(err.response?.data?.detail || "Erro ao deletar quarto.");
            }
        }
        setDeleteConfirmOpen(false);
        setRoomToDelete(null);
    }

    const cancelDeleteRoom = () => {
        setDeleteConfirmOpen(false);
        setRoomToDelete(null);
    }

    return (
        <Box
            sx={{
                backgroundColor: "#000",
                minHeight: "100vh",
                padding: 2,
                color: "#fff",
                position: "relative"
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
                    {error}
                </Alert>
            )}

            {/* Botão Adicionar Quarto no canto inferior direito */}
            <Button
                onClick={() => {
                    fetchDevices();
                    setDialogOpen(true);
                }}
                variant="contained"
                sx={{
                    backgroundColor: "#4CAF50",
                    color: "#fff",
                    position: 'fixed',
                    bottom: 16,
                    right: 16
                }}
            >
                Adicionar Quarto
            </Button>

            {/* Dialog para Adicionar Quarto */}
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

                    <Typography variant="body1">Selecionar Dispositivos:</Typography>
                    <Box sx={{ maxHeight: 200, overflowY: "auto" }}>
                        {availableDevices.map((device) => (
                            <Box key={device.id} sx={{ display: "flex", alignItems: "center" }}>
                                <input
                                    type="checkbox"
                                    checked={selectedDevices.some(d => d.id === device.id)}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setSelectedDevices([...selectedDevices, device]);
                                        } else {
                                            setSelectedDevices(selectedDevices.filter(d => d.id !== device.id));
                                        }
                                    }}
                                />
                                <Typography sx={{ marginLeft: 1 }}>{device.name}</Typography>
                            </Box>
                        ))}
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)} sx={{ color: "#fff", backgroundColor: "#f44336" }}>Cancelar</Button>
                    <Button onClick={handleAddRoom} sx={{ color: "#fff", backgroundColor: "#4CAF50" }}>Adicionar</Button>
                </DialogActions>
            </Dialog>

            {/* Dialog de confirmação para deletar quarto */}
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
                    <Button onClick={cancelDeleteRoom} sx={{ color: "#fff", backgroundColor: "#f44336" }}>Cancelar</Button>
                    <Button onClick={confirmDeleteRoom} sx={{ color: "#fff", backgroundColor: "#4CAF50" }}>Confirmar</Button>
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
                    const hasDoNotDisturb = room.devices.some(
                        (d) => d.states.do_not_disturb === "ON"
                    );
                    const hasCleaning = room.devices.some(
                        (d) => d.states.cleaning === "ON"
                    );
                    const isActive = room.devices.some(
                        (d) => d.states.bell === "ON"
                    );

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

                            {/* Ícone Não Perturbe */}
                            <Box sx={{ marginBottom: "16px" }}>
                                <IconButton
                                    onClick={(e) => {
                                        e.stopPropagation(); // Impede o clique no card
                                        if (!hasCleaning && room.devices[0]) {
                                            handleAction(
                                                room.devices[0].id,
                                                "doNotDisturb",
                                                hasDoNotDisturb ? "ON" : "OFF"
                                            );
                                        }
                                        hasDoNotDisturb
                                            ? console.log("Nao Perturbe Desativando...")
                                            : console.log("Nao Perturbe Ativando...");
                                    }}
                                    disabled={hasCleaning} // Desativa botão se Limpeza está ativada
                                    sx={{
                                        cursor: hasCleaning ? "not-allowed" : "pointer",
                                    }}
                                >
                                    <DoNotDisturbIcon
                                        sx={{
                                            fontSize: 50,
                                            color: hasDoNotDisturb
                                                ? "green"
                                                : "lightgray",
                                        }}
                                    />
                                </IconButton>
                                <Typography variant="body2">Não Perturbe</Typography>
                            </Box>

                            {/* Ícone Limpeza */}
                            <Box sx={{ marginBottom: "16px" }}>
                                <IconButton
                                    onClick={(e) => {
                                        e.stopPropagation(); // Impede o clique no card
                                        if (!hasDoNotDisturb && room.devices[0]) {
                                            handleAction(
                                                room.devices[0].id,
                                                "cleaning",
                                                hasCleaning ? "ON" : "OFF"
                                            );
                                        }
                                        hasCleaning
                                            ? console.log("Limpeza Desativando...")
                                            : console.log("Limpeza Ativando...");
                                    }}
                                    disabled={hasDoNotDisturb} // Desativa botão se Não Perturbe está ativado
                                    sx={{
                                        cursor: hasDoNotDisturb ? "not-allowed" : "pointer",
                                    }}
                                >
                                    <CleaningServicesIcon
                                        sx={{
                                            fontSize: 50,
                                            color: hasCleaning ? "green" : "lightgray",
                                        }}
                                    />
                                </IconButton>
                                <Typography variant="body2">Limpeza</Typography>
                            </Box>

                            {/* Ícone Campainha */}
                            <Box sx={{ marginBottom: "16px" }}>
                                <IconButton
                                    onClick={(e) => {
                                        e.stopPropagation(); // Impede o clique no card
                                        if (room.devices[0]) {
                                            handleAction(
                                                room.devices[0].id,
                                                "bell",
                                                isActive ? "ON" : "OFF"
                                            );
                                        }
                                        isActive
                                            ? console.log("Campainha Desativando...")
                                            : console.log("Campainha Ativando...");
                                    }}
                                    sx={{
                                        cursor: "pointer",
                                    }}
                                >
                                    <NotificationsActiveIcon
                                        sx={{
                                            fontSize: 50,
                                            color: isActive ? "green" : "lightgray",
                                        }}
                                    />
                                </IconButton>
                                <Typography variant="body2">Campainha</Typography>
                            </Box>

                            {/* Botao Deletar Quarto */}
                            <Box>
                               <Button
                                    onClick={(e) => {
                                        e.stopPropagation(); // Impede o clique no botão de disparar o evento do card
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