import React, { useState, createContext, ReactNode } from 'react';

// Define the context and the type of its value
interface CountdownContextType {
  timeLeft: string;
  setTimeLeft: (value: string) => void;
}

export const CountdownContext = createContext<CountdownContextType | undefined>(undefined);

export const CountdownProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [timeLeft, setTimeLeft] = useState('');

  return (
    <CountdownContext.Provider value={{ timeLeft, setTimeLeft }}>
      {children}
    </CountdownContext.Provider>
  );
};
