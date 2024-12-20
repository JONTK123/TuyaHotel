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

// import React, { useEffect, useState, useRef } from "react";
// import {
//     Box,
//     CircularProgress,
//     Typography,
//     Alert,
//     Button,
//     Card,
// } from "@mui/material";
// import { useParams } from "react-router-dom";
// import axios from "axios";
// import Notification from "./Notification";
//
// import LightbulbIcon from "@mui/icons-material/Lightbulb";
// import ToggleOnIcon from "@mui/icons-material/ToggleOn";
//
// const Devices = () => {
//     const { roomId } = useParams(); // Captura o roomId da URL
//     const [devices, setDevices] = useState<any[]>([]);
//     const [loading, setLoading] = useState(true);
//     const [error, setError] = useState("");
//     const [notifications, setNotifications] = useState<string[]>([]);
//     const wsRef = useRef<WebSocket | null>(null);
//
//     useEffect(() => {
//         const connectWebSocket = () => {
//             if (wsRef.current) {
//                 wsRef.current.close();
//             }
//
//             setDevices([]);
//             setError("");
//             setLoading(true);
//
//             wsRef.current = new WebSocket(
//                 `ws://localhost:8000/ws/device_panel/${roomId}`
//             );
//
//             wsRef.current.onopen = () => {
//                 setLoading(false);
//             };
//
//             wsRef.current.onmessage = (event) => {
//                 try {
//                     const data = JSON.parse(event.data);
//
//                     if (data.type === "error") {
//                         setError(data.data);
//                         setDevices([]);
//                     } else if (data.type === "device_state" && data.data) {
//                         setDevices(data.data);
//                     } else if (data.type === "pulsar_notification") {
//                         setNotifications((prev) => [
//                             ...prev,
//                             `Atualização recebida: ${JSON.stringify(data.data)}`,
//                         ].slice(-10));
//                     }
//                 } catch (error) {
//                     setError("Erro ao processar os dados do WebSocket.");
//                 }
//             };
//
//             wsRef.current.onerror = () => {
//                 setError("Erro ao conectar ao WebSocket.");
//                 setLoading(false);
//             };
//
//             wsRef.current.onclose = () => {
//                 console.log(`Conexão encerrada para o quarto ${roomId}.`);
//             };
//         };
//
//         connectWebSocket();
//
//         return () => {
//             if (wsRef.current) {
//                 wsRef.current.close();
//             }
//         };
//     }, [roomId]); // Atualiza o WebSocket quando o roomId muda
//
//     const handleAction = async (
//         device_id: string,
//         stateKey: string,
//         currentState: string,
//         action: string
//     ) => {
//         try {
//             const endpoints: { [key: string]: string } = {
//                 switch: currentState === "ON"
//                     ? `/api/devices/${device_id}/switch_off`
//                     : `/api/devices/${device_id}/switch_on`,
//                 doNotDisturb: currentState === "ON"
//                     ? `/api/devices/${device_id}/DoNotDisturbDeactivate`
//                     : `/api/devices/${device_id}/DoNotDisturbActivate`,
//                 cleaning: currentState === "ON"
//                     ? `/api/devices/${device_id}/CleaningDeactivate`
//                     : `/api/devices/${device_id}/CleaningActivate`,
//                 bell: currentState === "ON"
//                     ? `/api/devices/${device_id}/BellDeactivate`
//                     : `/api/devices/${device_id}/BellActivate`,
//                 freeze: `/api/devices/${device_id}/freeze`,
//                 unfreeze: `/api/devices/${device_id}/unfreeze`,
//                 turnOff: `/api/devices/${device_id}/turn-off`,
//             };
//
//             const endpoint = `http://localhost:8000${endpoints[action]}`;
//
//             // Se a ação for freeze/unfreeze/turnOff (sem estado definido), basta chamar o endpoint sem properties específicas:
//             if (["freeze", "unfreeze", "turnOff"].includes(action)) {
//                 await axios.post(endpoint);
//             } else {
//                 await axios.post(endpoint, {
//                     properties: { [stateKey]: currentState === "ON" ? false : true },
//                 });
//             }
//
//         } catch (err: any) {
//             setError(err.response?.data?.detail || "Erro na comunicação com o servidor.");
//         }
//     };
//
//     const removeNotification = (index: number) => {
//         setNotifications((prev) => prev.filter((_, i) => i !== index));
//     };
//
//     const getDeviceIcon = (category: string) => {
//         switch (category) {
//             case "lamp":
//                 return <LightbulbIcon sx={{ fontSize: 40, marginRight: 1 }} />;
//             case "light_switch":
//                 return <ToggleOnIcon sx={{ fontSize: 40, marginRight: 1 }} />;
//             default:
//                 return null;
//         }
//     };
//
//     // Função auxiliar para definir estilo do botão de ligar/desligar
//     const getButtonStyle = (currentState: string, actionOnText: string, actionOffText: string) => {
//         // Se estado atual é ON, o botão vai desligar => botão vermelho
//         // Se estado atual é OFF, o botão vai ligar => botão verde
//         if (currentState === "ON") {
//             return {
//                 text: actionOffText,
//                 sx: { backgroundColor: "red", color: "#fff" }
//             };
//         } else {
//             return {
//                 text: actionOnText,
//                 sx: { backgroundColor: "green", color: "#fff" }
//             };
//         }
//     };
//
//     return (
//         <Box sx={{ padding: 2, backgroundColor: "#000", minHeight: "100vh" }}>
//             <Typography variant="h5" gutterBottom sx={{ color: "#fff" }}>
//                 Dispositivos do Quarto {roomId}
//             </Typography>
//
//             {notifications.map((notification, index) => (
//                 <Notification
//                     key={index}
//                     message={notification}
//                     onClose={() => removeNotification(index)}
//                 />
//             ))}
//
//             {loading && (
//                 <Box display="flex" justifyContent="center" alignItems="center" height="300px">
//                     <CircularProgress sx={{ color: "#fff" }} />
//                 </Box>
//             )}
//
//             {error && (
//                 <Alert severity="error" style={{ margin: "20px" }}>
//                     {error}
//                 </Alert>
//             )}
//
//             {!loading && !error && devices.map((device, index) => {
//                 const { states } = device;
//
//                 return (
//                     <Card
//                         key={index}
//                         sx={{
//                             border: "1px solid #ccc",
//                             padding: 2,
//                             marginBottom: 2,
//                             display: "flex",
//                             flexDirection: "column",
//                             gap: 1,
//                             backgroundColor: "#333",
//                             color: "#fff",
//                         }}
//                     >
//                         <Box display="flex" alignItems="center">
//                             {getDeviceIcon(device.category)}
//                             <Typography variant="h6" sx={{ color: "#fff" }}>{device.name}</Typography>
//                         </Box>
//                         <Typography>Categoria: {device.category}</Typography>
//                         <Typography>Online: {device.Online ? "Sim" : "Não"}</Typography>
//
//                         {Object.keys(device.states).map((key) => (
//                             <Typography key={key}>
//                                 {key}: {device.states[key]}
//                             </Typography>
//                         ))}
//
//                         <Box sx={{ display: "flex", gap: 2, marginTop: "10px", flexWrap: "wrap" }}>
//                             {/* switch_led */}
//                             {states["switch_led"] !== undefined && (() => {
//                                 const { text, sx } = getButtonStyle(
//                                     states["switch_led"],
//                                     "Ligar Luz",
//                                     "Desligar Luz"
//                                 );
//                                 return (
//                                     <Button
//                                         variant="contained"
//                                         sx={sx}
//                                         onClick={() =>
//                                             handleAction(
//                                                 device.id,
//                                                 "switch_led",
//                                                 states["switch_led"],
//                                                 "switch"
//                                             )
//                                         }
//                                     >
//                                         {text}
//                                     </Button>
//                                 );
//                             })()}
//
//                             {/* do_not_disturb */}
//                             {states["do_not_disturb"] !== undefined && (() => {
//                                 const { text, sx } = getButtonStyle(
//                                     states["do_not_disturb"],
//                                     "Ativar Não Perturbe",
//                                     "Desativar Não Perturbe"
//                                 );
//                                 return (
//                                     <Button
//                                         variant="contained"
//                                         sx={sx}
//                                         disabled={states["cleaning"] === "ON"}
//                                         onClick={() =>
//                                             handleAction(
//                                                 device.id,
//                                                 "do_not_disturb",
//                                                 states["do_not_disturb"],
//                                                 "doNotDisturb"
//                                             )
//                                         }
//                                     >
//                                         {text}
//                                     </Button>
//                                 );
//                             })()}
//
//                             {/* cleaning */}
//                             {states["cleaning"] !== undefined && (() => {
//                                 const { text, sx } = getButtonStyle(
//                                     states["cleaning"],
//                                     "Ativar Limpeza",
//                                     "Desativar Limpeza"
//                                 );
//                                 return (
//                                     <Button
//                                         variant="contained"
//                                         sx={sx}
//                                         disabled={states["do_not_disturb"] === "ON"}
//                                         onClick={() =>
//                                             handleAction(
//                                                 device.id,
//                                                 "cleaning",
//                                                 states["cleaning"],
//                                                 "cleaning"
//                                             )
//                                         }
//                                     >
//                                         {text}
//                                     </Button>
//                                 );
//                             })()}
//
//                             {/* bell */}
//                             {states["bell"] !== undefined && (() => {
//                                 const { text, sx } = getButtonStyle(
//                                     states["bell"],
//                                     "Ativar Campainha",
//                                     "Desativar Campainha"
//                                 );
//                                 return (
//                                     <Button
//                                         variant="contained"
//                                         sx={sx}
//                                         onClick={() =>
//                                             handleAction(
//                                                 device.id,
//                                                 "bell",
//                                                 states["bell"],
//                                                 "bell"
//                                             )
//                                         }
//                                     >
//                                         {text}
//                                     </Button>
//                                 );
//                             })()}
//
//                             {/* freeze/unfreeze */}
//                             {states["freeze"] !== undefined && (
//                                 states["freeze"] === "ON"
//                                     ? (
//                                         <Button
//                                             variant="contained"
//                                             sx={{ backgroundColor: "red", color: "#fff" }}
//                                             onClick={() =>
//                                                 handleAction(
//                                                     device.id,
//                                                     "freeze",
//                                                     "ON",
//                                                     "unfreeze"
//                                                 )
//                                             }
//                                         >
//                                             Desativar Freeze
//                                         </Button>
//                                     ) : (
//                                         <Button
//                                             variant="contained"
//                                             sx={{ backgroundColor: "green", color: "#fff" }}
//                                             onClick={() =>
//                                                 handleAction(
//                                                     device.id,
//                                                     "freeze",
//                                                     "OFF",
//                                                     "freeze"
//                                                 )
//                                             }
//                                         >
//                                             Ativar Freeze
//                                         </Button>
//                                     )
//                             )}
//
//                             {/* turnOff */}
//                             {/* Supondo que turnOff é sempre válido para desligar o dispositivo.
//                                 O botão será sempre vermelho, pois a ação é de desligar. */}
//                             <Button
//                                 variant="contained"
//                                 sx={{ backgroundColor: "red", color: "#fff" }}
//                                 onClick={() =>
//                                     handleAction(
//                                         device.id,
//                                         "main_switch",
//                                         "ON",
//                                         "turnOff"
//                                     )
//                                 }
//                             >
//                                 Desligar Dispositivo
//                             </Button>
//                         </Box>
//                     </Card>
//                 );
//             })}
//         </Box>
//     );
// };
//
// export default Devices;
