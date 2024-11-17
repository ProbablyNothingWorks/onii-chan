import React from 'react';
import { Box, Container, Typography, Paper, Alert } from '@mui/material';
import Image from 'next/image';

export const Description = () => {
  return (
    <Container maxWidth='lg'>
      <Box sx={{ pb: 8 }}>
        {/* Hero Section */}
        <Box
          sx={{
            width: '100%',
            position: 'relative',
            height: '400px',
            borderRadius: '16px',
            mb: 6,
            overflow: 'hidden'
          }}
        >
          <Image
            src='/idol-anime-oshi-no-ko.jpg.webp'
            alt='Help cultivate and train the next generation of virtual idols!'
            fill
            style={{ objectFit: 'cover' }}
            priority
          />
        </Box>

        {/* Manage Section */}
        <Paper
          elevation={3}
          sx={{
            p: 4,
            mb: 6,
            borderRadius: '16px'
          }}
        >
          <Typography
            variant='h4'
            gutterBottom
            sx={{
              fontWeight: 'bold',

              textAlign: 'center',
              mb: 3
            }}
          >
            Manage A Virtual Idol!
          </Typography>
          <Box sx={{ maxWidth: '800px', mx: 'auto' }}>
            <Typography variant='body1' paragraph>
              You are a talent agency manager and the company just assigned you
              their latest talent: a virtual idol!
            </Typography>
            <Typography variant='body1' paragraph>
              The idol just started her career and doesn't know much about the
              world. You will be responsible for teaching her new skills,
              dealing with fans, and growing her popularity.
            </Typography>
            <Typography variant='body1' paragraph>
              Your idol is counting on you for guidance, making the right
              business decisions, and becoming a star!
            </Typography>
            <Typography
              variant='h6'
              sx={{
                textAlign: 'center',
                color: '#e74c3c',
                mt: 3
              }}
            >
              頑張ってね!
            </Typography>
          </Box>
        </Paper>
        {/* YouTube Video Section */}
        <Paper
          elevation={3}
          sx={{
            p: 4,
            mb: 6,
            borderRadius: '16px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center'
          }}
        >
          <Typography
            variant='h4'
            gutterBottom
            sx={{
              fontWeight: 'bold',
              textAlign: 'center',
              mb: 3
            }}
          >
            Our Demo
          </Typography>
          <Box
            sx={{
              position: 'relative',
              width: '100%',
              maxWidth: '800px',
              paddingTop: '56.25%', // 16:9 Aspect Ratio
              mb: 2
            }}
          >
            <iframe
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                borderRadius: '8px'
              }}
              src="https://www.youtube.com/embed/9IIBlChBsRk"
              title="Virtual Idol Manager Demo"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </Box>
        </Paper>

        {/* Features Section */}
        <Box
          sx={{
            mb: 6,
            background: '#2c3e50',
            borderRadius: '16px',
            p: 4,
            color: 'white'
          }}
        >
          <Typography
            variant='h5'
            gutterBottom
            sx={{
              color: 'white',
              textAlign: 'center',
              mb: 4,
              fontWeight: 'bold'
            }}
          >
            Gameplay Features
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 3,
              justifyContent: 'center'
            }}
          >
            {[
              {
                primary: 'Grow Your Fan Base',
                secondary:
                  'Gain real world fans for your idol with social media'
              },
              {
                primary: 'Learn Skills',
                secondary:
                  'Teach your idol the latest trends or new skills to attract more fans'
              },
              {
                primary: 'Business Growth',
                secondary:
                  'Help your idol win over advertisers and business contracts'
              }
            ].map((feature, index) => (
              <Paper
                key={index}
                sx={{
                  p: 3,
                  flex: '1 1 300px',
                  maxWidth: '350px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '12px'
                }}
              >
                <Typography variant='h6' sx={{ color: 'white', mb: 1 }}>
                  {feature.primary}
                </Typography>
                <Typography
                  variant='body2'
                  sx={{ color: 'rgba(255, 255, 255, 0.8)' }}
                >
                  {feature.secondary}
                </Typography>
              </Paper>
            ))}
          </Box>
        </Box>

        {/* Disclaimer Section */}
        <Alert
          severity='info'
          sx={{
            borderRadius: '16px',
            '& .MuiAlert-message': {
              width: '100%'
            }
          }}
        >
          <Typography variant='body2'>
            This is an alpha release, so expect lots of bugs. Please contact us
            at{' '}
            <a
              href='https://x.com/Prob0Wrks'
              target='_blank'
              rel='noopener noreferrer'
              style={{ color: '#1976d2' }}
            >
              https://x.com/Prob0Wrks
            </a>{' '}
            for more information.
          </Typography>
        </Alert>
      </Box>
    </Container>
  );
};

export default Description;
