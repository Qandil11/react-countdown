import React, { useEffect, useContext } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { CountdownContext } from './CountdownContext';

const CountdownApp = () => {
  const countdownContext = useContext(CountdownContext);

  if (!countdownContext) {
    throw new Error('CountdownApp must be used within a CountdownProvider');
  }

  const { timeLeft, setTimeLeft } = countdownContext;

  useEffect(() => {
    const targetDate = new Date('2024-12-31T00:00:00'); // Set your target date here
    const interval = setInterval(() => {
      const now = new Date();
      const difference = targetDate.getTime() - now.getTime();

      if (difference <= 0) {
        clearInterval(interval);
        setTimeLeft('Countdown finished!');
      } else {
        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((difference / 1000 / 60) % 60);
        const seconds = Math.floor((difference / 1000) % 60);
        setTimeLeft(`${days}d ${hours}h ${minutes}m ${seconds}s`);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [setTimeLeft]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Countdown to New Year!</Text>
      <Text style={styles.countdown}>{timeLeft}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#282c34',
  },
  title: {
    fontSize: 24,
    color: '#ffffff',
    marginBottom: 20,
  },
  countdown: {
    fontSize: 32,
    color: '#61dafb',
  },
});

export default CountdownApp;
