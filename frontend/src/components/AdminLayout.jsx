import { Outlet, Link, useLocation } from "react-router-dom";
import {
  Show,
  UserButton,
  OrganizationSwitcher,
  useOrganization,
  useUser,
} from "@clerk/react";
import ThemeToggler from "../utils/ThemeToggler";
import UnauthorizedPage from "../pages/Unauthorized";

function AdminLayout() {
  const { organization, membership } = useOrganization();
  const { user } = useUser();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <Show when={"signed-in"}>
      {/* Protect ensures user is admin inside organization */}
      <Show
        when={{ SignedIn: true, role: "org:admin" }}
        fallback={<UnauthorizedPage />}
      >
        <div className="min-h-screen flex w-full dark:bg-gray-900 bg-gray-50">
          {/* Sidebar */}
          <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col justify-between max-h-screen">
            <div>
              <div className="p-6 flex items-center justify-between">
                <h1 className="text-[22px] font-bold text-gray-800 dark:text-white">
                  AI Management
                </h1>

                <ThemeToggler />
              </div>

              {/* Organization Switcher */}
              <div className="px-4 pb-4 dark:text-white">
                <OrganizationSwitcher
                  hidePersonal
                  afterCreateOrganizationUrl="/admin"
                  afterSelectOrganizationUrl="/admin"
                  createOrganizationMode="modal"
                  appearance={{
                    elements: {
                      userPreviewMainIdentifierText__personalWorkspace: {
                        color: "white",
                      },
                      organizationPreviewMainIdentifier__organizationSwitcherTrigger:
                        { color: "green" },
                    },
                  }}
                />
              </div>

              <nav className="mt-2 space-y-1 px-3">
                <Link
                  to="/admin/finetuning"
                  className={`w-full flex px-3 py-2 text-sm rounded-md ${
                    isActive("/admin/finetuning")
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-900/50"
                      : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  }`}
                >
                  Model Training
                </Link>

                <Link
                  to="/user/project"
                  className={`w-full flex px-3 py-2 text-sm rounded-md ${
                    isActive("/admin/users")
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-900/50"
                      : "text-gray-700 dark:bg-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-500"
                  }`}
                >
                  Chat Interface
                </Link>
              </nav>
            </div>

            {/* User profile */}
            <div className="p-4 border-t border-gray-700 dark:border:gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3 overflow-hidden">
                <div>
                  <UserButton
                    size={18}
                    className="text-blue-600 dark:text-blue-300"
                  />
                </div>

                <div className="truncate">
                  <div className="text-sm font-medium dark:text-gray-200">
                    {user?.fullName} {`(${membership?.role})`}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.primaryEmailAddress?.emailAddress}
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* Main */}
          <main className="flex-1 overflow-y-scroll">
            <div className="py-8 px-8 sm:px-10 max-w-5xl mx-auto">
              {organization ? <Outlet /> : <p>Select an organization</p>}
            </div>
          </main>
        </div>
      </Show>
    </Show>
  );
}

export default AdminLayout;
