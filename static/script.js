const loginForm = document.querySelector('#login-form');

loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = loginForm.querySelector('#username').value;
    const password = loginForm.querySelector('#password').value;

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            window.location.href = '/dashboard'; // Redirect to the dashboard upon successful login
        } else {
            const errorMessage = await response.text();
            alert(errorMessage); // Display error message if login fails
        }
    } catch (error) {
        console.error('Error during login:', error);
        alert('An error occurred during login. Please try again later.');
    }
});