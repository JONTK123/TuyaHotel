import React from "react";
import { Container, Box } from "@mui/material";
import Rooms from "../components/Rooms";

const Dashboard = () => {
    return (
        <Box
            sx={{
                backgroundColor: "#000", // Fundo preto
                minHeight: "100vh", // Garante que o fundo preto cubra toda a altura da tela
                padding: 2,
            }}
        >
            <Container sx={{ marginTop: 4 }}>
                <Rooms />
            </Container>
        </Box>
    );
};

export default Dashboard;
