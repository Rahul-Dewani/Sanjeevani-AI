import * as React from 'react';
import DarkModeIcon from '@mui/icons-material/DarkModeRounded';
import LightModeIcon from '@mui/icons-material/LightModeRounded';
import IconButton, { IconButtonOwnProps } from '@mui/material/IconButton';
import { useColorScheme } from '@mui/material/styles';

export default function ColorModeIconToggle(props: IconButtonOwnProps) {
  const { mode, setMode } = useColorScheme();
  const [mounted, setMounted] = React.useState(false);

  // Ensure the component is mounted to avoid hydration issues
  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    // Render a placeholder while waiting for the component to mount
    return (
      <IconButton
        aria-label="toggle light/dark mode"
        size="small"
        disabled
        sx={{
          width: '2.25rem',
          height: '2.25rem',
        }}
      >
        {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
      </IconButton>
    );
  }

  return (
    <IconButton
      aria-label="toggle light/dark mode"
      size="small"
      onClick={() => setMode(mode === 'light' ? 'dark' : 'light')}
      sx={{
        width: '2.25rem',
        height: '2.25rem',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: (theme) => theme.shape.borderRadius,
        backgroundColor: mode === 'light' ? 'white' : 'black',
        color: mode === 'light' ? 'black' : 'white',
        '&:hover': {
          backgroundColor: mode === 'light' ? 'grey.200' : 'grey.800',
        },
      }}
      {...props}
    >
      {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
    </IconButton>
  );
}
