'use client';

import * as React from 'react';
import { cn } from '../../utils/cn';
import { CortexLink } from './CortexLink';
import { SuiteSwitcher } from './SuiteSwitcher';
import { NavigationProps, UserProfile } from '../../types/navigation';
import { useNavigationContext } from '../../hooks/useNavigation';
import { Button } from '../button';
import { Input } from '../input';

/**
 * GlobalNavigation - Persistent navigation bar across all domains
 *
 * Features:
 * - Sinergy logo linking to platform
 * - Suite switcher dropdown
 * - Links to Designer and Marketplace
 * - Global search
 * - User profile menu
 *
 * Layout:
 * +--------------------------------------------------------------------+
 * | [Logo] CORTX | Suites | Designer | Marketplace | [Search] | [User] |
 * +--------------------------------------------------------------------+
 *
 * Usage:
 * ```tsx
 * <GlobalNavigation
 *   user={{
 *     name: "John Doe",
 *     email: "john@example.com",
 *     avatarUrl: "/avatar.jpg"
 *   }}
 *   onSearch={(query) => console.log('Search:', query)}
 *   onSignOut={() => console.log('Sign out')}
 * />
 * ```
 */

export interface GlobalNavigationProps extends NavigationProps {
  /** User profile information */
  user?: UserProfile;
  /** Callback when search is performed */
  onSearch?: (query: string) => void;
  /** Callback when user signs out */
  onSignOut?: () => void;
  /** Whether to show the search bar */
  showSearch?: boolean;
}

export function GlobalNavigation({
  user,
  onSearch,
  onSignOut,
  showSearch = true,
  showMobile = false,
  className,
}: GlobalNavigationProps) {
  const { currentDomain } = useNavigationContext();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch && searchQuery.trim()) {
      onSearch(searchQuery.trim());
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  return (
    <nav
      className={cn(
        'sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
        className
      )}
    >
      <div className="container flex h-16 items-center justify-between px-4">
        {/* Logo and Platform Link */}
        <div className="flex items-center gap-6">
          <CortexLink
            to="platform-dashboard"
            className="flex items-center gap-2 hover:opacity-80"
          >
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-md bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="font-bold text-lg hidden sm:inline">CORTX</span>
            </div>
          </CortexLink>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-4">
            {/* Suite Switcher */}
            <SuiteSwitcher currentDomain={currentDomain} />

            {/* Platform Tools */}
            <div className="flex items-center gap-2">
              <CortexLink to="platform-designer">
                <Button variant="ghost" size="sm">
                  Designer
                </Button>
              </CortexLink>
              <CortexLink to="platform-marketplace">
                <Button variant="ghost" size="sm">
                  Marketplace
                </Button>
              </CortexLink>
              <CortexLink to="platform-thinktank">
                <Button variant="ghost" size="sm">
                  ThinkTank
                </Button>
              </CortexLink>
            </div>
          </div>
        </div>

        {/* Right Side - Search and User */}
        <div className="flex items-center gap-4">
          {/* Search Bar */}
          {showSearch && (
            <form
              onSubmit={handleSearch}
              className="hidden lg:flex items-center"
            >
              <div className="relative">
                <Input
                  type="search"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                  className="w-[200px] xl:w-[300px] pr-8"
                />
                <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 hidden h-5 select-none items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
                  <span className="text-xs">⌘</span>K
                </kbd>
              </div>
            </form>
          )}

          {/* User Menu */}
          {user && (
            <div className="flex items-center gap-2">
              <div className="hidden md:flex flex-col items-end">
                <span className="text-sm font-medium">{user.name}</span>
                <span className="text-xs text-muted-foreground">
                  {user.role || user.email}
                </span>
              </div>
              <div className="relative">
                {user.avatarUrl ? (
                  <img
                    src={user.avatarUrl}
                    alt={user.name}
                    className="h-8 w-8 rounded-full object-cover border-2 border-border"
                  />
                ) : (
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center border-2 border-border">
                    <span className="text-white text-sm font-medium">
                      {user.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Mobile Menu Toggle */}
          {showMobile && (
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {isMobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </Button>
          )}
        </div>
      </div>

      {/* Mobile Menu */}
      {showMobile && isMobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-background">
          <div className="container py-4 px-4 space-y-4">
            {/* Mobile Suite Switcher */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Switch Suite
              </label>
              <SuiteSwitcher currentDomain={currentDomain} />
            </div>

            {/* Mobile Platform Links */}
            <div className="space-y-2">
              <CortexLink to="platform-designer">
                <Button variant="ghost" className="w-full justify-start">
                  Designer
                </Button>
              </CortexLink>
              <CortexLink to="platform-marketplace">
                <Button variant="ghost" className="w-full justify-start">
                  Marketplace
                </Button>
              </CortexLink>
              <CortexLink to="platform-thinktank">
                <Button variant="ghost" className="w-full justify-start">
                  ThinkTank
                </Button>
              </CortexLink>
            </div>

            {/* Mobile Search */}
            {showSearch && (
              <form onSubmit={handleSearch} className="pt-2">
                <Input
                  type="search"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                  className="w-full"
                />
              </form>
            )}

            {/* Mobile Sign Out */}
            {user && onSignOut && (
              <Button
                variant="outline"
                className="w-full"
                onClick={onSignOut}
              >
                Sign Out
              </Button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}

GlobalNavigation.displayName = 'GlobalNavigation';
