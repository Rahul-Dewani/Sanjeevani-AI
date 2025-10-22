import React from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './ToastifyStyles.css'; // Custom styles for Toastify
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import MuiCard from '@mui/material/Card';
import Checkbox from '@mui/material/Checkbox';
import Divider from '@mui/material/Divider';
import FormLabel from '@mui/material/FormLabel';
import { IconButton, InputAdornment } from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import Link from '@mui/material/Link';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';
import ForgotPassword from './ForgotPassword';
import { useNavigate } from 'react-router-dom';
import { GoogleIcon, FacebookIcon, SitemarkIcon } from './CustomIcons';

const Card = styled(MuiCard)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignSelf: 'center',
  width: '100%',
  padding: theme.spacing(4),
  gap: theme.spacing(2),
  backgroundColor: 'var(--white)',
  boxShadow: '0px 5px 15px rgba(0, 0, 0, 0.05), 0px 15px 35px -5px rgba(0, 0, 0, 0.05)',
  borderRadius: '12px',
  transition: 'all 0.3s ease-in-out',
  [theme.breakpoints.up('sm')]: {
    width: '450px',
  },
  '&:hover': {
    boxShadow: '0px 5px 15px rgba(0, 0, 0, 0.1), 0px 15px 35px -5px rgba(0, 0, 0, 0.1)',
  },
  ...theme.applyStyles('dark', {
    backgroundColor: 'var(--dark-bg)',
    color: 'var(--dark-text)',
    boxShadow: '0px 5px 15px var(--dark-highlight), 0px 15px 35px -5px rgba(0, 0, 0, 0.08)',
    '&:hover': {
      backgroundColor: 'var(--dark-hover)',
    },
  }),
}));


export default function SignInCard() {
  const [isSignUp, setIsSignUp] = React.useState(false);
  const [emailError, setEmailError] = React.useState(false);
  const [emailErrorMessage, setEmailErrorMessage] = React.useState('');
  const [passwordError, setPasswordError] = React.useState(false);
  const [passwordErrorMessage, setPasswordErrorMessage] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [email, setEmail] = React.useState("");
  const [otp, setOtp] = React.useState("");
  const [isEmailVerified, setIsEmailVerified] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);
  const [password, setPassword] = React.useState(""); // Add password state
  const navigate = useNavigate();

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };


  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };


  const handleSendOTP = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/send-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const result = await response.json();
      if (response.ok) {
        toast.success("OTP sent successfully!");
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      toast.error("Error sending OTP.");
    }
  };

  const handleVerifyOTP = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
      const result = await response.json();
      if (response.ok) {
        setIsEmailVerified(true);
        toast.success("Email verified successfully!");
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      toast.error("Error verifying OTP.");
    }
  };

  const validateInputs = () => {
    const email = document.getElementById('email') as HTMLInputElement;
    const password = document.getElementById('password') as HTMLInputElement;

    let isValid = true;

    if (!email.value || !/\S+@\S+\.\S+/.test(email.value)) {
      setEmailError(true);
      setEmailErrorMessage('Please enter a valid email address.');
      toast.error('Invalid email address.');
      isValid = false;
    } else {
      setEmailError(false);
      setEmailErrorMessage('');
    }

    if (!password.value || password.value.length < 6) {
      setPasswordError(true);
      setPasswordErrorMessage('Password must be at least 6 characters long.');
      toast.error('Password must be at least 6 characters long.');
      isValid = false;
    } else {
      setPasswordError(false);
      setPasswordErrorMessage('');
    }

    return isValid;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!validateInputs()) return;

    const data = new FormData(event.currentTarget);

    const payload = isSignUp
      ? {
        firstName: data.get('firstName'),
        lastName: data.get('lastName'),
        phone: data.get('phone'),
        email: data.get('email'),
        password: data.get('password'),
      }
      : {
        email: data.get('email'),
        password: data.get('password'),
      };

    const endpoint = isSignUp
      ? 'http://127.0.0.1:5000/signup'
      : 'http://127.0.0.1:5000/signin';

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await response.json();
      if (response.ok) {
        toast.success(isSignUp ? 'Sign-up successful!' : 'Sign-in successful!');
        sessionStorage.setItem('doctorId', result.id);
        navigate('/dashboard');
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Something went wrong. Please try again.');
    }
  };



  return (
    <>
      <Card variant="outlined">
        <Typography
          component="h1"
          variant="h4"
          sx={{ width: '100%', fontSize: 'clamp(2rem, 10vw, 2.15rem)' }}
        >
          {isSignUp ? 'Sign Up' : 'Sign In'}
        </Typography>
        <Box
          component="form"
          onSubmit={handleSubmit}
          noValidate
          sx={{ display: 'flex', flexDirection: 'column', width: '100%', gap: 2 }}
        >
          <FormControl fullWidth>
  <FormLabel htmlFor="email">Email</FormLabel>
  <TextField
    error={emailError}
    helperText={emailErrorMessage}
    id="email"
    type="email"
    name="email"
    placeholder="your@email.com"
    required
    fullWidth
    value={email}
    onChange={(e) => setEmail(e.target.value)}
    InputProps={{
      endAdornment: isSignUp ? (
        <InputAdornment position="end">
          <Button 
            onClick={handleSendOTP} 
            variant="contained" 
            size="small"
            sx={{ 
              textTransform: "none",
              fontSize: "0.85rem",
              padding: "6px 12px",
              borderRadius: "8px",
            }}
          >
            Send OTP
          </Button>
        </InputAdornment>
      ) : null,
    }}
  />
</FormControl>


          {isSignUp && !isEmailVerified ? (
            <Box sx={{  display: 'flex', flexDirection: 'column', width: '100%'}}>
              {/* <Button onClick={handleSendOTP} variant="contained">
                Send OTP
              </Button> */}
              <FormLabel htmlFor="otp">OTP</FormLabel>
              <TextField
                // label="Enter OTP"
                fullWidth
                placeholder='Enter OTP'
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <Button 
                        onClick={handleVerifyOTP} 
                        variant="contained" 
                        size="small"
                        sx={{ 
                          textTransform: "none",
                          fontSize: "0.85rem",
                          padding: "6px 12px",
                          borderRadius: "8px",
                        }}
                      >
                        Verify OTP
                      </Button>
                    </InputAdornment>
                  ),
                }}
              />
              {/* <Button onClick={handleVerifyOTP} variant="contained">
                Verify
              </Button> */}
            </Box>
          ) : isSignUp ? (
            <>
              <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
                <FormControl sx={{ flex: 1 }}>
                  <FormLabel htmlFor="firstName">First Name</FormLabel>
                  <TextField id="firstName" name="firstName" required fullWidth />
                </FormControl>
                <FormControl sx={{ flex: 1 }}>
                  <FormLabel htmlFor="lastName">Last Name</FormLabel>
                  <TextField id="lastName" name="lastName" required fullWidth />
                </FormControl>
              </Box>
              <FormControl>
                <FormLabel htmlFor="phone">Phone Number</FormLabel>
                <TextField id="phone" name="phone" type="tel" required fullWidth />
              </FormControl>
              <FormControl>
                <FormLabel htmlFor="setPassword">Set Password</FormLabel>
                <TextField
                  error={passwordError}
                  helperText={passwordErrorMessage}
                  id="password"
                  type={showPassword ? "text" : "password"} // Toggle visibility
                  name="password"
                  required
                  fullWidth
                  value={password} // Link to state
                  onChange={(e) => setPassword(e.target.value)} // Update state on change
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={togglePasswordVisibility}
                          edge="end"
                          sx={{
                            backgroundColor: "transparent", // Removes background
                            border: "none", // Ensures no border
                            padding: 0, // Removes extra padding
                            minWidth: "auto", // Prevents unwanted spacing
                            "&:hover": { backgroundColor: "transparent" }, // No hover effect
                            "&:focus": { outline: "none" }, // Removes focus border
                            "&:active": { backgroundColor: "transparent" }, // No active state
                            boxShadow: "none", // Ensures no shadow
                          }}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </FormControl>
            </>
          ) : (
            <FormControl>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <FormLabel htmlFor="password">Password</FormLabel>
                <Link component="button" type="button" onClick={handleClickOpen} variant="body2">
                  Forgot your password?
                </Link>
              </Box>
              <TextField
                error={passwordError}
                helperText={passwordErrorMessage}
                id="password"
                type={showPassword ? "text" : "password"} // Toggle visibility
                name="password"
                required
                fullWidth
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={togglePasswordVisibility}
                        edge="end"
                        sx={{
                          backgroundColor: "transparent", // Removes background
                          border: "none", // Ensures no border
                          padding: 0, // Removes extra padding
                          minWidth: "auto", // Prevents unwanted spacing
                          "&:hover": { backgroundColor: "transparent" }, // No hover effect
                          "&:focus": { outline: "none" }, // Removes focus border
                          "&:active": { backgroundColor: "transparent" }, // No active state
                          boxShadow: "none", // Ensures no shadow
                        }}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </FormControl>
          )}

          {!isSignUp && (
            <FormControlLabel control={<Checkbox value="remember" color="primary" />} label="Remember me" />
          )}
          <ForgotPassword open={open} handleClose={handleClose} />
          <Button type="submit" fullWidth variant="contained" disabled={isSignUp && !isEmailVerified}>
            {isSignUp ? 'Sign Up' : 'Sign In'}
          </Button>
          <Typography sx={{ textAlign: 'center' }}>
            {isSignUp ? 'Already have an account? ' : "Don't have an account? "}
            <span>
              <Link
                component="button"
                type="button"
                onClick={() => setIsSignUp(!isSignUp)}
                variant="body2"
              >
                {isSignUp ? 'Sign in' : 'Sign up'}
              </Link>
            </span>
          </Typography>
        </Box>
        <Divider>or</Divider>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Button fullWidth variant="outlined" onClick={() => toast.error('Sign in with Google')} startIcon={<GoogleIcon />}>
            {isSignUp ? 'Sign up with Google' : 'Sign in with Google'}
          </Button>
          <Button fullWidth variant="outlined" onClick={() => toast.error('Sign in with Facebook')} startIcon={<FacebookIcon />}>
            {isSignUp ? 'Sign up with Facebook' : 'Sign in with Facebook'}
          </Button>
        </Box>
      </Card>
    </>
  );


}
