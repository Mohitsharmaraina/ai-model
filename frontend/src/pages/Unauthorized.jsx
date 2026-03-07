import { SignInButton } from "@clerk/react";
import { Lock } from "lucide-react";

function UnauthorizedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6 bg-gray-50 dark:bg-gray-900 transition-colors">
      <div className="max-w-md w-full text-center bg-white dark:bg-gray-800 shadow-lg rounded-xl p-10 border border-gray-200 dark:border-gray-700">
        {/* Icon */}
        <div className="mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900 mb-6">
          <Lock className="text-blue-600 dark:text-blue-300" size={28} />
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          Access Restricted
        </h1>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          You are not authorized to access this page. Please sign in to continue
          to the application.
        </p>

        {/* Sign In Button */}
        <SignInButton mode="modal">
          <button className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors">
            Sign In
          </button>
        </SignInButton>
      </div>
    </div>
  );
}

export default UnauthorizedPage;
