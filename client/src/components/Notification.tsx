import React, { useEffect } from "react";
import { Box, Typography, IconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

interface NotificationProps {
    message: string;
    onClose: () => void;
    duration?: number; // Duração opcional em milissegundos
}

const Notification: React.FC<NotificationProps> = ({ message, onClose, duration = 3000 }) => {
    useEffect(() => {
        const timer = setTimeout(onClose, duration);
        return () => clearTimeout(timer); // Limpa o timer quando o componente é desmontado
    }, [onClose, duration]);

    return (
        <Box
            sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "16px",
                backgroundColor: "#f8d7da",
                color: "#721c24",
                border: "1px solid #f5c6cb",
                borderRadius: "4px",
                marginBottom: "16px",
            }}
        >
            <Typography>{message}</Typography>
            <IconButton onClick={onClose}>
                <CloseIcon />
            </IconButton>
        </Box>
    );
};

export default Notification;
