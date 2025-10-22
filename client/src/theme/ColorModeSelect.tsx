import * as React from 'react';
import { useColorScheme } from '@mui/material/styles';
import IconButton, { IconButtonProps } from '@mui/material/IconButton';
import DarkModeIcon from '@mui/icons-material/DarkModeRounded';
import LightModeIcon from '@mui/icons-material/LightModeRounded';

export default function ColorModeToggleButton(props: IconButtonProps) {
  const { mode, setMode } = useColorScheme();

  // Ensure `mode` and `setMode` exist before rendering
  if (!mode || !setMode) {
    return null;
  }

  return (
    <IconButton
      aria-label="toggle light/dark mode"
      onClick={() => setMode(mode === 'light' ? 'dark' : 'light')}
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: (theme) => theme.shape.borderRadius,
        backgroundColor: mode === 'light' ? 'white' : 'black',
        color: mode === 'light' ? 'black' : 'white',
        '&:hover': {
          backgroundColor: mode === 'light' ? 'grey.200' : 'grey.800',
        },
        width: '2.25rem',
        height: '2.25rem',
      }}
      {...props}
    >
      {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
    </IconButton>
  );
}
