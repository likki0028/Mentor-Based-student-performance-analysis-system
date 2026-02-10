
import React from 'react';

const AlertBox = ({ type, message }) => {
    return (
        <div style={{
            padding: '1rem',
            margin: '1rem 0',
            border: '1px solid',
            borderColor: type === 'error' ? 'red' : 'green',
            backgroundColor: type === 'error' ? '#ffe6e6' : '#e6ffe6'
        }}>
            {message}
        </div>
    );
};

export default AlertBox;
