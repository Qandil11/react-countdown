import React from 'react';
import { CountdownProvider } from './CountdownContext';
import CountdownApp from './CountdownApp';

const App = () => {
  return (
    <CountdownProvider>
      <CountdownApp />
    </CountdownProvider>
  );
};

export default App;
