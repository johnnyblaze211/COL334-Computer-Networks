#ifndef TCPNEWRENOCSE_H
#define TCPNEWRENOCSE_H

#include "ns3/tcp-congestion-ops.h"
#include "ns3/tcp-recovery-ops.h"
//yo
namespace ns3 {
class TcpNewRenoCSE: public TcpNewReno
{
public:
	static TypeId GetTypeId(void);

	TcpNewRenoCSE (void);

	TcpNewRenoCSE (const TcpNewRenoCSE& sock);
	virtual ~TcpNewRenoCSE(void);

	virtual std::string GetName () const;

	virtual uint32_t GetSsThresh (Ptr<const TcpSocketState> tcb,
                                uint32_t bytesInFlight);
	virtual void IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);

	virtual Ptr<TcpCongestionOps> Fork();

protected:
	virtual uint32_t SlowStart (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
	virtual void CongestionAvoidance (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);
};

}	// namespace ns3

#endif