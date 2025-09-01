// Initialize Firebase
firebase.initializeApp(window.firebaseConfig);

const auth = firebase.auth();
const signInButton = document.getElementById('signInButton');
const signOutButton = document.getElementById('signOutButton');
const authMessage = document.getElementById('authMessage');

// Listen for auth state changes
auth.onAuthStateChanged((user) => {
    if (user) {
        // User is signed in
        authMessage.textContent = `Signed in as ${user.displayName || user.email}`;
        signInButton.style.display = 'none';
        signOutButton.style.display = 'inline-block';
    } else {
        // User is signed out
        authMessage.textContent = 'Not signed in';
        signInButton.style.display = 'inline-block';
        signOutButton.style.display = 'none';
    }
});

// Sign In with Google
signInButton.addEventListener('click', () => {
    const provider = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(provider)
        .then((result) => {
            // Signed in
            console.log('User signed in:', result.user);

            // Get the ID token
            const idToken = await result.user.getIdToken();

            // Exchange ID token for session cookie
            const sessionLoginResponse = await fetch('/sessionLogin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idToken: idToken }),
                credentials: 'include' // IMPORTANT: send cookies with the request
            });

            if (sessionLoginResponse.ok) {
                console.log("Session cookie set successfully.");
                // Redirect or update UI upon successful session login
                window.location.href = '/articles'; // Example redirect
            } else {
                const errorData = await sessionLoginResponse.json();
                console.error("Failed to set session cookie:", errorData.error || sessionLoginResponse.statusText);
                alert("Login failed: Could not establish session. " + (errorData.error || "Unknown error."));
            }
        })
        .catch((error) => {
            console.error('Error during sign in:', error);
        });
});

// Sign Out
signOutButton.addEventListener('click', () => {
    auth.signOut()
        .then(() => {
            console.log('User signed out');
        })
        .catch((error) => {
            console.error('Error during sign out:', error);
        });
});
