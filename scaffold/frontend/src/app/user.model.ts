export interface UserView {
  id: string;
  email: string;
  role: 'OWNER' | 'ADMIN' | 'MEMBER';
  status: 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  purgeAt?: string;
}
