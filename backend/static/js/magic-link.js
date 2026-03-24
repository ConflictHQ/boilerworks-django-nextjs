
const magic = new Magic('pk_live_99833148D15FE4E5');

const login = (() => {

  const element = name => document.getElementById(name)

  const loggedIn = async (didToken) => {
    element("id_did_token").setAttribute('value', didToken);
    element("login-form").submit();
  }

  const addLoginForm = async () => {
  }

  const onLoad = async () => {
    const isLoggedIn = await magic.user.isLoggedIn();
    if (isLoggedIn) {
      const didToken = await magic.user.getIdToken();
      //await loggedIn(didToken)
    } else {
      //element("checking").setAttribute('hidden', 'true');
      //element("login-form").removeAttribute('hidden');
      await addLoginForm();
    }
  }

  const authenticate = async () => {
    const email = 'testuser@example.com'; //element("email").value;
    if (email) {
      const didToken = await magic.auth.loginWithMagicLink({email});
      await loggedIn(didToken)
    }
  }

  return {
    onLoad: onLoad,
    authenticate: authenticate,
    loggedIn: loggedIn,
  }

})()

window.onload = () => login.onLoad()
