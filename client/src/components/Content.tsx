import * as React from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import  MedicalServicesRoundedIcon  from '@mui/icons-material/MedicalServicesRounded';
import  ManageAccountsRoundedIcon  from '@mui/icons-material/ManageAccountsRounded';
import  DashboardCustomizeRoundedIcon  from '@mui/icons-material/DashboardCustomizeRounded';
import  SecurityRoundedIcon  from '@mui/icons-material/SecurityRounded';
import { SitemarkIcon } from './CustomIcons';

const items = [
  {
    icon: <MedicalServicesRoundedIcon sx={{ color: 'text.secondary' }} />,
    title: 'AI-Powered Diagnosis',
    description:
      'Upload medical images and receive AI-driven disease predictions along with expert recommendations.',
},
{
    icon: <ManageAccountsRoundedIcon sx={{ color: 'text.secondary' }} />,
    title: 'Effortless Patient Management',
    description:
      'Securely store and manage patient records with an integrated database system tailored for doctors.',
},
{
    icon: <DashboardCustomizeRoundedIcon sx={{ color: 'text.secondary' }} />,
    title: 'Intuitive Dashboard',
    description:
      'Navigate seamlessly with an easy-to-use interface that simplifies report generation and data access.',
},
{
    icon: <SecurityRoundedIcon sx={{ color: 'text.secondary' }} />,
    title: 'Data Security & Compliance',
    description:
      'Ensure patient confidentiality with robust security measures and compliance with medical standards.',
},


];

export default function Content() {
  return (
    <Stack
      sx={{ flexDirection: 'column', alignSelf: 'center', gap: 4, maxWidth: 450 }}
    >
      <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
        <img src="./logo-name.png" width={"300px"} alt="logo" />
      </Box>
      {items.map((item, index) => (
        <Stack key={index} direction="row" sx={{ gap: 2 }}>
          {item.icon}
          <div>
            <Typography gutterBottom sx={{ fontWeight: 'medium' }}>
              {item.title}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {item.description}
            </Typography>
          </div>
        </Stack>
      ))}
    </Stack>
  );
}
