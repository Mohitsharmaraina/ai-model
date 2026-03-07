import React from "react";
import { SignIn } from "@clerk/react";
const SignInPage = () => {
  return (
    <div>
      <SignIn routing="path" path="/sign-in" signInUrl="/sign-in" />
    </div>
  );
};

export default SignInPage;
