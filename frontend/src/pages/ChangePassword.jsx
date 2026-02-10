
import React, { useState } from 'react';

const ChangePassword = () => {
    const [password, setPassword] = useState('');

    const handleChange = () => {
        // TODO: Call API
        alert('Password change stub');
    };

    return (
        <div>
            <h1>Change Password</h1>
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="New Password"
            />
            <button onClick={handleChange}>Update</button>
        </div>
    );
};

export default ChangePassword;
