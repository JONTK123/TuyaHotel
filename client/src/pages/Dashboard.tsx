import React from "react";
import {Typography, Container} from "@mui/material";
import Devices from "../components/Devices";

const Dashboard = () => {
     return (
        <Container sx={{ marginTop: 4 }}>
          <Typography variant="h4" gutterBottom>
            Painel de Dispositivos
          </Typography>
          <Devices/>
        </Container>
     );
};

export default Dashboard;