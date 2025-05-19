// Login Form Submission
document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault();
    alert('Login Successful! Redirecting to Account Page...');
    window.location.href = 'account.html';
  });
  
  // Transfer Form Submission
  document.getElementById('transferForm').addEventListener('submit', function (e) {
    e.preventDefault();
    alert('Transfer Successful!');
  });