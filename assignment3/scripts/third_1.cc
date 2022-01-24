/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <fstream>
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("FifthScriptExample");

// ===========================================================================
//
//         node 0                 node 1
//   +----------------+    +----------------+
//   |    ns-3 TCP    |    |    ns-3 TCP    |
//   +----------------+    +----------------+
//   |    10.1.1.1    |    |    10.1.1.2    |
//   +----------------+    +----------------+
//   | point-to-point |    | point-to-point |
//   +----------------+    +----------------+
//           |                     |
//           +---------------------+
//                5 Mbps, 2 ms
//
//
// We want to look at changes in the ns-3 TCP congestion window.  We need
// to crank up a flow and hook the CongestionWindow attribute on the socket
// of the sender.  Normally one would use an on-off application to generate a
// flow, but this has a couple of problems.  First, the socket of the on-off 
// application is not created until Application Start time, so we wouldn't be 
// able to hook the socket (now) at configuration time.  Second, even if we 
// could arrange a call after start time, the socket is not public so we 
// couldn't get at it.
//
// So, we can cook up a simple version of the on-off application that does what
// we want.  On the plus side we don't need all of the complexity of the on-off
// application.  On the minus side, we don't have a helper, so we have to get
// a little more involved in the details, but this is trivial.
//
// So first, we create a socket and do the trace connect on it; then we pass 
// this socket into the constructor of our simple application which we then 
// install in the source node.
// ===========================================================================
//

int droppedPackets_1_3 = 0;
int droppedPackets_2_3 = 0;
class MyApp : public Application 
{
public:

  MyApp ();
  virtual ~MyApp();

  static TypeId GetTypeId(void);
  void Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate);

private:
  virtual void StartApplication (void);
  virtual void StopApplication (void);

  void ScheduleTx (void);
  void SendPacket (void);

  Ptr<Socket>     m_socket;
  Address         m_peer;
  uint32_t        m_packetSize;
  uint32_t        m_nPackets;
  DataRate        m_dataRate;
  EventId         m_sendEvent;
  bool            m_running;
  uint32_t        m_packetsSent;
};

MyApp::MyApp ()
  : m_socket (0), 
    m_peer (), 
    m_packetSize (0), 
    m_nPackets (0), 
    m_dataRate (0), 
    m_sendEvent (), 
    m_running (false), 
    m_packetsSent (0)
{
}

MyApp::~MyApp()
{
  m_socket = 0;
}

/* static */
TypeId MyApp::GetTypeId(void)
{
    static TypeId tid = TypeId("MyApp")
                            .SetParent<Application>()
                            .SetGroupName("Tutorial")
                            .AddConstructor<MyApp>();
    return tid;
}

void
MyApp::Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate)
{
  m_socket = socket;
  m_peer = address;
  m_packetSize = packetSize;
  m_nPackets = nPackets;
  m_dataRate = dataRate;
}

void
MyApp::StartApplication (void)
{
  m_running = true;
  m_packetsSent = 0;
  m_socket->Bind ();
  m_socket->Connect (m_peer);
  SendPacket ();
}

void 
MyApp::StopApplication (void)
{
  m_running = false;

  if (m_sendEvent.IsRunning ())
    {
      Simulator::Cancel (m_sendEvent);
    }

  if (m_socket)
    {
      m_socket->Close ();
    }
}

void 
MyApp::SendPacket (void)
{
  Ptr<Packet> packet = Create<Packet> (m_packetSize);
  m_socket->Send (packet);

  if (++m_packetsSent < m_nPackets)
    {
      ScheduleTx ();
    }
}

void 
MyApp::ScheduleTx (void)
{
  if (m_running)
    {
      Time tNext (Seconds (m_packetSize * 8 / static_cast<double> (m_dataRate.GetBitRate ())));
      m_sendEvent = Simulator::Schedule (tNext, &MyApp::SendPacket, this);
    }
}

static void
CwndChange (Ptr<OutputStreamWrapper> stream, uint32_t oldCwnd, uint32_t newCwnd)
{
  NS_LOG_UNCOND (Simulator::Now ().GetSeconds () << "\t" << newCwnd);
  *stream->GetStream()<<Simulator::Now().GetSeconds()<<"\t"<<newCwnd<<std::endl;
}

static void
RxDrop_1_3 (Ptr<const Packet> p)
{
  //NS_LOG_UNCOND ("RxDrop at " << Simulator::Now ().GetSeconds ());
  droppedPackets_1_3++;
}

static void
RxDrop_2_3 (Ptr<const Packet> p)
{
  //NS_LOG_UNCOND ("RxDrop at " << Simulator::Now ().GetSeconds ());
  droppedPackets_2_3++;
}

int 
main (int argc, char *argv[])
{
  
  
  CommandLine cmd;
  int configuration = 1;
  cmd.AddValue("configuration", "Configuration must be 1, 2 or 3", configuration);
  cmd.Parse (argc, argv);


  if(configuration!=1 && configuration!=2 && configuration!=3){
    NS_LOG_UNCOND("Unrecognized TCP protocol");
    return 1;
  }

  //return 0;
  
  
  NodeContainer nodes;
  nodes.Create(3);
  Ptr<Node> N1 = nodes.Get(0);
  Ptr<Node> N2 = nodes.Get(1);
  Ptr<Node> N3 = nodes.Get(2);

  PointToPointHelper ch_1_3, ch_2_3;
  ch_1_3.SetDeviceAttribute("DataRate", StringValue("10Mbps"));
  ch_1_3.SetChannelAttribute("Delay", StringValue("3ms"));
  ch_2_3.SetDeviceAttribute("DataRate", StringValue("9Mbps"));
  ch_2_3.SetChannelAttribute("Delay", StringValue("3ms"));

  NetDeviceContainer dev_1_3, dev_2_3;
  dev_1_3 = ch_1_3.Install(N1, N3);
  //node_2_3.Add(node_1_3.Get(1));
  dev_2_3 = ch_2_3.Install(N2, N3);


  Ptr<RateErrorModel> em = CreateObject<RateErrorModel> ();
  em->SetAttribute ("ErrorRate", DoubleValue (0.00001));
  dev_1_3.Get (1)->SetAttribute ("ReceiveErrorModel", PointerValue (em));

  //Ptr<RateErrorModel> em2 = CreateObject<RateErrorModel> ();
  //em2->SetAttribute ("ErrorRate", DoubleValue (0.00001));
  dev_2_3.Get (1)->SetAttribute ("ReceiveErrorModel", PointerValue (em));


  
  NetDeviceContainer allDevices = NetDeviceContainer(dev_1_3, dev_2_3);


  InternetStackHelper stack;
  stack.Install (N1);
  stack.Install (N2);
  stack.Install (N3);

  Ipv4AddressHelper addressHelper1, addressHelper2;
  addressHelper1.SetBase ("10.0.0.0", "255.255.255.0");
  addressHelper2.SetBase ("10.1.2.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces_1_3 = addressHelper1.Assign (dev_1_3);
  Ipv4InterfaceContainer interfaces_2_3 = addressHelper2.Assign (dev_2_3);


  uint16_t sinkPort1 = 8080;
  Address sinkAddress1 (InetSocketAddress (interfaces_1_3.GetAddress (1), sinkPort1));
  Address sinkAddress2 (InetSocketAddress (interfaces_2_3.GetAddress (1), sinkPort1));
  

  PacketSinkHelper psh1("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), sinkPort1));
  ApplicationContainer sinkApp1 = psh1.Install(N3);
  sinkApp1.Start(Seconds(0.));
  sinkApp1.Stop(Seconds(30.));

  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(TcpNewReno::GetTypeId()));

  std::stringstream N1_id_str, N2_id_str, N3_id_str;
  N1_id_str<<N1->GetId(); N2_id_str<<N2->GetId(); N3_id_str<<N3->GetId();
  std::string s1 = "/NodeList/"+N1_id_str.str() + "/$ns3::TcpL4Protocol/SocketType";
  std::string s2 = "/NodeList/"+N2_id_str.str() + "/$ns3::TcpL4Protocol/SocketType";
  std::string s3 = "/NodeList/"+N3_id_str.str() + "/$ns3::TcpL4Protocol/SocketType";
  
  TypeId tid = TypeId::LookupByName("ns3::TcpNewRenoCSE");
  if (configuration == 2){
    Config::Set(s2, TypeIdValue(tid));
  }

  else if(configuration == 3){
    
    Config::Set(s1, TypeIdValue(tid));
    Config::Set(s2, TypeIdValue(tid));
    Config::Set(s3, TypeIdValue(tid));
  }
  

  Ptr<Socket> N1_sock1 = Socket::CreateSocket(N1, TcpSocketFactory::GetTypeId());

  Ptr<Socket> N1_sock2 = Socket::CreateSocket(N1, TcpSocketFactory::GetTypeId());

  Ptr<Socket> N2_sock1 = Socket::CreateSocket(N2, TcpSocketFactory::GetTypeId());

  AsciiTraceHelper asciihelper;
  Ptr<OutputStreamWrapper> stream = asciihelper.CreateFileStream("scratch/Q3_N1_sock1_config" + std::to_string(configuration)+".txt");
  Ptr<OutputStreamWrapper> stream2 = asciihelper.CreateFileStream("scratch/Q3_N1_sock2_config"+std::to_string(configuration)+".txt");
  Ptr<OutputStreamWrapper> stream3 = asciihelper.CreateFileStream("scratch/Q3_N2_sock1_config"+std::to_string(configuration)+".txt");
  
  
  
  Ptr<MyApp> app = CreateObject<MyApp>();
  app->Setup(N1_sock1, sinkAddress1, 3000, 100000, DataRate("1.5Mbps"));
  N1->AddApplication(app);
  app->SetStartTime(Seconds (1.));
  app->SetStopTime(Seconds(20.));

  Ptr<MyApp> app2 = CreateObject<MyApp>();
  app2->Setup(N1_sock2, sinkAddress1, 3000, 100000, DataRate("1.5Mbps"));
  N1->AddApplication(app2);
  app2->SetStartTime(Seconds (5.));
  app2->SetStopTime(Seconds(25.));

  Ptr<MyApp> app3 = CreateObject<MyApp>();
  app3->Setup(N2_sock1, sinkAddress2, 3000, 100000, DataRate("1.5Mbps"));
  N2->AddApplication(app3);
  app3->SetStartTime(Seconds(15.));
  app3->SetStopTime(Seconds(30.));

  N1_sock1->TraceConnectWithoutContext("CongestionWindow", MakeBoundCallback(&CwndChange, stream));
  N1_sock2->TraceConnectWithoutContext("CongestionWindow", MakeBoundCallback(&CwndChange, stream2));
  N2_sock1->TraceConnectWithoutContext("CongestionWindow", MakeBoundCallback(&CwndChange, stream3));

  dev_1_3.Get (1)->TraceConnectWithoutContext("PhyRxDrop", MakeCallback(&RxDrop_1_3));
  dev_2_3.Get (1)->TraceConnectWithoutContext("PhyRxDrop", MakeCallback(&RxDrop_2_3));

  Simulator::Stop (Seconds (40.));
  Simulator::Run ();
  Simulator::Destroy ();


  NS_LOG_UNCOND("No. of Dropped Packets: for Connection N1----N3: "<<droppedPackets_1_3);
  NS_LOG_UNCOND("No. of Dropped Packets: for Connection N2----N3: "<<droppedPackets_2_3);

  system(("python3 scratch/third_2.py " + std::to_string(configuration)).c_str());
  //system("rm scratch/*.txt");

  /*
  Ptr<Socket> ns3TcpSocket = Socket::CreateSocket (nodes.Get (0), TcpSocketFactory::GetTypeId ());
  AsciiTraceHelper asciihelper;
  Ptr<OutputStreamWrapper> stream = asciihelper.CreateFileStream("scratch/"+TcpL4Protocol+".txt");
  ns3TcpSocket->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream));

  Ptr<MyApp> app = CreateObject<MyApp> ();
  app->Setup (ns3TcpSocket, sinkAddress, 3000, 10000, DataRate ("1Mbps"));
  nodes.Get (0)->AddApplication (app);
  app->SetStartTime (Seconds (1.));
  app->SetStopTime (Seconds (30.));

  devices.Get (1)->TraceConnectWithoutContext ("PhyRxDrop", MakeCallback (&RxDrop));

  
  

  system(("python3 scratch/script1.py " + TcpL4Protocol).c_str());
  system("rm scratch/\\*.txt");

  return 0;*/
}

