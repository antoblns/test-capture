import { useEffect, useState } from "react";
import reactLogo from "./assets/react.svg";
import "./App.css";

function useCapture() {
    const [count, setCount] = useState(0);
    useEffect(() => {
        // vite dev makes it two appearancies here i.e. 2 connections. Use yarn build yarn preview.
        const websocket = new WebSocket("ws://localhost:8765/ws");
        websocket.onmessage = async (event) => {
            setCount((count) => count + 1);
            console.log(event.data);
        };
    }, []);
    return count;
}
function Capture() {
    const count = useCapture();
    // Getting new image can be done in 1000 ways incl. binary over ws. 
    return <img src={`http://localhost:8765/image?q=${count}`} width={500} />;
}
function App() {
    const [count, setCount] = useState(0);

    return (
        <div className="App">
            <Capture />
            <div className="card">
                <button onClick={() => setCount((count) => count + 1)}>
                    count is {count}
                </button>
                <p>
                    Edit <code>src/App.tsx</code> and save to test HMR
                </p>
            </div>
            <p className="read-the-docs">
                Click on the Vite and React logos to learn more
            </p>
        </div>
    );
}

export default App;
